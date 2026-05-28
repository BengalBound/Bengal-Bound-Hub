import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.resume_after_permission")
def resume_after_permission(perm_request_pk: int):
    """
    Called after a human approves or denies an AgentPermissionRequest.
    Resets the agent instance to idle, logs the decision, and attempts
    to route to the agent's own webhooks.handle_permission_resume() if it exists.
    """
    from agents.models import AgentPermissionRequest, AgentLog

    try:
        perm = AgentPermissionRequest.objects.select_related(
            'instance', 'instance__catalog'
        ).get(pk=perm_request_pk)
    except AgentPermissionRequest.DoesNotExist:
        logger.error("resume_after_permission: AgentPermissionRequest #%s not found", perm_request_pk)
        return

    instance = perm.instance
    decision = perm.decision

    # Log the outcome
    log = AgentLog.objects.create(
        instance=instance,
        action=f"permission_respond #{perm.pk}",
        outcome='success' if decision == 'approved' else 'failed',
        detail=(
            f"Human decision: {decision}.\n"
            f"Context: {perm.context}\n"
            f"Option A: {perm.option_a}\n"
            f"Option B: {perm.option_b}"
        ),
    )

    # Link log back to permission request
    if not perm.log:
        perm.log = log
        perm.executed = True
        perm.save(update_fields=['log', 'executed'])

    # Try agent-specific resume hook
    try:
        import importlib
        slug = instance.catalog.slug.replace('-', '_')
        agent_module = importlib.import_module(f'agents.{slug}.webhooks')
        if hasattr(agent_module, 'handle_permission_resume'):
            agent_module.handle_permission_resume(perm, instance)
    except (ImportError, AttributeError):
        pass  # agent has no resume hook — next beat cycle will re-evaluate
    except Exception as exc:
        logger.error("resume_after_permission: agent hook failed for instance %s: %s", instance.pk, exc)

    # Reset instance so Celery Beat picks it up again
    if instance.status == 'waiting':
        instance.status = 'idle'
        instance.save(update_fields=['status'])

    logger.info(
        "resume_after_permission: instance %s (%s) decision=%s",
        instance.pk, instance.catalog.name, decision,
    )
