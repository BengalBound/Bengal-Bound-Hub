"""
Generic agent API views — shared by all 30 agents.
Each agent slug gets: run / logs / status / approvals / decide
"""
import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from hub.models import BusinessInstance, BusinessEmployee
from .models import AgentCatalog, AgentInstance, AgentLog, AgentPermissionRequest

logger = logging.getLogger(__name__)


def _get_instance(request, slug, agent_slug):
    """Validate business access, return (business, catalog, instance)."""
    business = get_object_or_404(BusinessInstance, slug=slug)
    get_object_or_404(BusinessEmployee, business=business, user=request.user, is_active=True)
    catalog = get_object_or_404(AgentCatalog, slug=agent_slug)
    instance, _ = AgentInstance.objects.get_or_create(
        business=business,
        catalog=catalog,
        defaults={'status': 'idle', 'config': {}},
    )
    return business, catalog, instance


class AgentStatusView(APIView):
    """GET /hub/<slug>/agents/<agent_slug>/status/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, slug, agent_slug):
        _, catalog, instance = _get_instance(request, slug, agent_slug)
        pending = AgentPermissionRequest.objects.filter(
            instance=instance, decision__isnull=True
        ).count()
        last_log = AgentLog.objects.filter(instance=instance).order_by('-created_at').first()
        return Response({
            'agent': catalog.name,
            'slug': catalog.slug,
            'icon': catalog.icon,
            'category': catalog.category,
            'status': instance.status,
            'tokens_used_this_month': instance.tokens_used_this_month,
            'last_run_at': instance.last_run_at,
            'pending_approvals': pending,
            'last_outcome': last_log.outcome if last_log else None,
            'last_action': last_log.action if last_log else None,
        })


class AgentLogsView(APIView):
    """GET /hub/<slug>/agents/<agent_slug>/logs/?limit=50"""
    permission_classes = [IsAuthenticated]

    def get(self, request, slug, agent_slug):
        _, catalog, instance = _get_instance(request, slug, agent_slug)
        limit = min(int(request.GET.get('limit', 50)), 200)
        logs = AgentLog.objects.filter(instance=instance).order_by('-created_at')[:limit]
        return Response([{
            'id': log.pk,
            'action': log.action,
            'outcome': log.outcome,
            'detail': log.detail[:800] if log.detail else '',
            'model_used': log.model_used,
            'tokens': log.tokens,
            'duration_ms': log.duration_ms,
            'created_at': log.created_at.isoformat(),
        } for log in logs])


class AgentRunView(APIView):
    """POST /hub/<slug>/agents/<agent_slug>/run/  — on-demand chat with the agent."""
    permission_classes = [IsAuthenticated]

    def post(self, request, slug, agent_slug):
        from agents.utils import agent_chat

        _, catalog, instance = _get_instance(request, slug, agent_slug)

        user_input = (request.data.get('input') or '').strip()
        if not user_input:
            return Response({'error': 'input is required'}, status=status.HTTP_400_BAD_REQUEST)

        instance.status = 'working'
        instance.save(update_fields=['status'])

        t0 = timezone.now()
        try:
            result = agent_chat([
                {'role': 'system', 'content': catalog.system_prompt},
                {'role': 'user',   'content': user_input},
            ])
            duration_ms = int((timezone.now() - t0).total_seconds() * 1000)
            log = AgentLog.objects.create(
                instance=instance,
                action='manual_run',
                outcome='success',
                detail=result,
                duration_ms=duration_ms,
            )
            instance.status = 'idle'
            instance.last_run_at = timezone.now()
            instance.save(update_fields=['status', 'last_run_at'])
            return Response({'result': result, 'log_id': log.pk, 'duration_ms': duration_ms})

        except Exception as exc:
            logger.error("AgentRunView %s/%s: %s", slug, agent_slug, exc)
            AgentLog.objects.create(
                instance=instance, action='manual_run',
                outcome='failed', detail=str(exc),
            )
            instance.status = 'idle'
            instance.save(update_fields=['status'])
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AgentApprovalsView(APIView):
    """GET /hub/<slug>/agents/<agent_slug>/approvals/  — pending permission requests."""
    permission_classes = [IsAuthenticated]

    def get(self, request, slug, agent_slug):
        _, catalog, instance = _get_instance(request, slug, agent_slug)
        pending = AgentPermissionRequest.objects.filter(
            instance=instance, decision__isnull=True
        ).order_by('-created_at')[:30]
        return Response([{
            'id': pr.pk,
            'context': pr.context,
            'option_a': pr.option_a,
            'option_b': pr.option_b,
            'created_at': pr.created_at.isoformat(),
        } for pr in pending])


class AgentDecideView(APIView):
    """POST /hub/<slug>/agents/<agent_slug>/approvals/<pk>/decide/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, slug, agent_slug, pk):
        _, _, instance = _get_instance(request, slug, agent_slug)
        pr = get_object_or_404(AgentPermissionRequest, pk=pk, instance=instance)

        if pr.decision is not None:
            return Response({'error': 'already decided'}, status=status.HTTP_409_CONFLICT)

        decision = request.data.get('decision')
        if decision not in ('approved', 'denied'):
            return Response(
                {'error': 'decision must be "approved" or "denied"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pr.decision = decision
        pr.decided_at = timezone.now()
        pr.decided_by = request.user
        pr.save(update_fields=['decision', 'decided_at', 'decided_by'])

        try:
            from agents.tasks import resume_after_permission
            resume_after_permission.delay(pr.pk)
        except Exception as exc:
            logger.warning("Could not queue resume_after_permission pk=%s: %s", pk, exc)

        return Response({'status': 'success', 'decision': decision})
