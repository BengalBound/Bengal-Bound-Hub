from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from agents.models import AgentWebhookEndpoint, AgentPermissionRequest
from agents.platform.webhook_receiver import WebhookReceiver
import json

@csrf_exempt
def inbound_webhook(request, token):
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    endpoint = get_object_or_404(AgentWebhookEndpoint, url_token=token, is_active=True)
    
    # Optional HMAC verification
    signature = request.headers.get('X-Hub-Signature-256', '').replace('sha256=', '')
    if endpoint.secret and not WebhookReceiver.verify_hmac(endpoint.secret, request.body, signature):
        return HttpResponse('Invalid signature', status=401)
    
    payload = json.loads(request.body)
    
    # Route to the agent's webhooks.py
    try:
        import importlib
        agent_module = importlib.import_module(f'agents.{endpoint.instance.catalog.slug}.webhooks')
        agent_module.handle_event('webhook_event', payload, endpoint.instance)
    except Exception as e:
        return JsonResponse({'status': 'error', 'detail': str(e)}, status=500)
    
    endpoint.event_count += 1
    endpoint.save(update_fields=['event_count'])
    
    return JsonResponse({'status': 'success'})

def permission_respond(request, pk):
    perm_request = get_object_or_404(AgentPermissionRequest, pk=pk)
    if request.method == 'POST':
        decision = request.POST.get('decision')
        if decision in ['approved', 'denied']:
            perm_request.decision = decision
            if request.user.is_authenticated:
                perm_request.decided_by = request.user
            from django.utils import timezone
            perm_request.decided_at = timezone.now()
            perm_request.save()
            
            # Resume agent logic here
            
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'invalid decision'}, status=400)
    
    return HttpResponse(f"Console UI for Permission Request {pk}. Current decision: {perm_request.decision}")
