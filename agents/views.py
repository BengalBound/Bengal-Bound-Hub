import json
import logging

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils import timezone

from agents.models import AgentWebhookEndpoint, AgentPermissionRequest, AgentLog
from agents.platform.webhook_receiver import WebhookReceiver

logger = logging.getLogger(__name__)


@csrf_exempt
def inbound_webhook(request, token):
    if request.method != 'POST':
        return HttpResponse(status=405)

    endpoint = get_object_or_404(AgentWebhookEndpoint, url_token=token, is_active=True)

    # HMAC verification (optional — skip if no secret configured)
    signature = request.headers.get('X-Hub-Signature-256', '').replace('sha256=', '')
    if endpoint.secret and not WebhookReceiver.verify_hmac(endpoint.secret, request.body, signature):
        return HttpResponse('Invalid signature', status=401)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse('Invalid JSON', status=400)

    try:
        import importlib
        agent_module = importlib.import_module(f'agents.{endpoint.instance.catalog.slug}.webhooks')
        agent_module.handle_event('webhook_event', payload, endpoint.instance)
    except Exception as exc:
        logger.error("inbound_webhook token=%s error: %s", token, exc)
        return JsonResponse({'status': 'error', 'detail': str(exc)}, status=500)

    endpoint.event_count += 1
    endpoint.last_triggered_at = timezone.now()
    endpoint.save(update_fields=['event_count', 'last_triggered_at'])

    return JsonResponse({'status': 'success'})


@csrf_exempt
def permission_respond(request, pk):
    perm_request = get_object_or_404(AgentPermissionRequest, pk=pk)

    if request.method == 'GET':
        return HttpResponse(
            f"<h2>Permission Request — {perm_request.instance.catalog.name}</h2>"
            f"<p><strong>Context:</strong> {perm_request.context}</p>"
            f"<p><strong>Option A:</strong> {perm_request.option_a}</p>"
            f"<p><strong>Option B:</strong> {perm_request.option_b or 'N/A'}</p>"
            f"<form method='post'>"
            f"<input type='hidden' name='csrfmiddlewaretoken' value=''>"
            f"<button name='decision' value='approved'>Approve</button> &nbsp;"
            f"<button name='decision' value='denied'>Deny</button>"
            f"</form>"
            f"<p>Current decision: {perm_request.decision or 'Pending'}</p>",
            content_type='text/html',
        )

    if request.method == 'POST':
        # Accept both JSON body and form POST
        try:
            body = json.loads(request.body)
            decision = body.get('decision')
        except (json.JSONDecodeError, AttributeError):
            decision = request.POST.get('decision')

        if decision not in ('approved', 'denied'):
            return JsonResponse({'status': 'error', 'detail': 'decision must be approved or denied'}, status=400)

        if perm_request.decision is not None:
            return JsonResponse({'status': 'error', 'detail': 'already decided'}, status=409)

        perm_request.decision = decision
        perm_request.decided_at = timezone.now()
        if request.user.is_authenticated:
            perm_request.decided_by = request.user
        perm_request.save(update_fields=['decision', 'decided_at', 'decided_by'])

        # Resume agent — fire background task
        try:
            from agents.tasks import resume_after_permission
            resume_after_permission.delay(perm_request.pk)
        except Exception as exc:
            logger.warning("Could not queue resume_after_permission for pk=%s: %s", pk, exc)
            # Fallback: reset instance directly so next beat cycle picks it up
            _reset_instance(perm_request)

        return JsonResponse({'status': 'success', 'decision': decision})

    return HttpResponse(status=405)


def _reset_instance(perm_request: AgentPermissionRequest):
    """Fallback: reset instance to idle so the next Celery Beat cycle resumes work."""
    instance = perm_request.instance
    if instance.status == 'waiting':
        instance.status = 'idle'
        instance.save(update_fields=['status'])
    AgentLog.objects.create(
        instance=instance,
        action=f"permission_respond #{perm_request.pk}",
        outcome='success' if perm_request.decision == 'approved' else 'failed',
        detail=f"Human decision: {perm_request.decision}. Context: {perm_request.context[:200]}",
    )
