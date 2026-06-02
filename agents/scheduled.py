"""
Shared helper for all scheduled LangChain agent tasks.

Usage in any agent's tasks.py:
    from agents.scheduled import run_scheduled_agent_task
    run_scheduled_agent_task(instance, 'task_name', 'prompt telling agent what to do')
"""
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def run_scheduled_agent_task(instance, task_name: str, task_prompt: str) -> str:
    """
    Run agent_chat() for a Celery background task, write an AgentLog,
    and post a UserNotification to the business owner's console bell.

    Handles status transitions (idle → working → idle) and catches all errors.
    Returns the agent's text response (or an error string).
    """
    from agents.utils import agent_chat
    from agents.models import AgentLog

    instance.status = 'working'
    instance.save(update_fields=['status'])

    t0 = timezone.now()
    try:
        result = agent_chat(
            messages=[
                {'role': 'system', 'content': instance.catalog.system_prompt},
                {'role': 'user',   'content': task_prompt},
            ],
            business=instance.business,
            agent_slug=instance.catalog.slug,
        )
        duration_ms = int((timezone.now() - t0).total_seconds() * 1000)

        AgentLog.objects.create(
            instance=instance,
            action=task_name,
            outcome='success',
            detail=result,
            duration_ms=duration_ms,
        )
        _notify_owner(instance, task_name, result)

        instance.status = 'idle'
        instance.last_run_at = timezone.now()
        instance.save(update_fields=['status', 'last_run_at'])
        logger.info("scheduled %s / %s: ok (%dms)", instance.catalog.slug, task_name, duration_ms)
        return result

    except Exception as exc:
        logger.error("scheduled %s / %s: %s", instance.catalog.slug, task_name, exc, exc_info=True)
        AgentLog.objects.create(
            instance=instance,
            action=task_name,
            outcome='failed',
            detail=str(exc),
        )
        instance.status = 'idle'
        instance.save(update_fields=['status'])
        return f"Error: {exc}"


def _notify_owner(instance, task_name: str, result: str) -> None:
    """Post a console bell notification to the business owner."""
    try:
        from workspace_admin.models import UserNotification
        owner = instance.business.owner
        if not owner:
            return
        summary = result[:300].replace('\n', ' ')
        if len(result) > 300:
            summary += '…'
        UserNotification.objects.create(
            user=owner,
            title=f"{instance.catalog.name}: {task_name.replace('_', ' ').title()}",
            message=summary,
        )
    except Exception as exc:
        logger.warning("_notify_owner failed for %s: %s", instance.business.slug, exc)
