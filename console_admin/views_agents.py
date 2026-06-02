"""
Console-facing agent workspace views.
"""
import logging
from django.shortcuts import render, get_object_or_404

from .decorators import console_user_required
from agents.models import AgentCatalog, AgentInstance, AgentLog, AgentPermissionRequest

logger = logging.getLogger(__name__)


def _get_console_biz(request):
    from hub.models import BusinessInstance
    return BusinessInstance.objects.filter(owner=request.user, is_active=True).first()


@console_user_required(login_url='/accounts/login/')
def agent_workspace(request, agent_slug):
    """Main workspace for a single agent — chat, logs, approvals."""
    catalog = get_object_or_404(AgentCatalog, slug=agent_slug, is_active=True)
    biz = _get_console_biz(request)

    instance = None
    logs = []
    pending_approvals = []

    if biz:
        instance, _ = AgentInstance.objects.get_or_create(
            business=biz,
            catalog=catalog,
            defaults={'status': 'idle', 'config': {}},
        )
        logs = AgentLog.objects.filter(instance=instance).order_by('-created_at')[:30]
        pending_approvals = AgentPermissionRequest.objects.filter(
            instance=instance, decision__isnull=True
        ).order_by('-created_at')

    return render(request, 'console_admin/agent_workspace.html', {
        'catalog': catalog,
        'instance': instance,
        'logs': logs,
        'pending_approvals': pending_approvals,
        'agent_slug': agent_slug,
    })


@console_user_required(login_url='/accounts/login/')
def agents_overview(request):
    """All hired agents for this business — activity dashboard."""
    biz = _get_console_biz(request)
    instances = []
    total_pending = 0

    if biz:
        instances = AgentInstance.objects.filter(
            business=biz
        ).select_related('catalog').order_by('catalog__category', 'catalog__name')
        total_pending = AgentPermissionRequest.objects.filter(
            instance__business=biz, decision__isnull=True
        ).count()

    all_agents = AgentCatalog.objects.filter(is_active=True).order_by('category', 'name')
    hired_slugs = {i.catalog.slug for i in instances}
    available_agents = all_agents.exclude(slug__in=hired_slugs)

    return render(request, 'console_admin/agents_overview.html', {
        'instances': instances,
        'all_agents': all_agents,
        'available_agents': available_agents,
        'hired_slugs': hired_slugs,
        'total_pending': total_pending,
    })
