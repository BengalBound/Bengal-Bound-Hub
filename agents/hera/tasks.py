import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.hera.overdue_onboarding_check")
def overdue_onboarding_check():
    from django.utils import timezone
    from agents.hera.models import OnboardingTask

    today = timezone.now().date()
    overdue = OnboardingTask.objects.filter(
        is_completed=False,
        due_date__lt=today,
    )
    count = overdue.count()
    for task in overdue:
        logger.warning("Hera: overdue onboarding task [%s] for %s (due: %s)",
                       task.task, task.employee_name, task.due_date)
    logger.info("hera.overdue_onboarding_check: %d overdue tasks", count)
    return count


@shared_task(name="agents.hera.auto_answer_pending_queries")
def auto_answer_pending_queries():
    from agents.hera.models import PolicyQuery
    from agents.hera.engine import HeraEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='hera')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = HeraEngine()
    answered = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        unanswered = PolicyQuery.objects.filter(business=instance.business, ai_answer="")
        for query in unanswered:
            try:
                query.ai_answer = engine.answer_policy_query(query, instance=instance)
                query.save(update_fields=["ai_answer"])
                answered += 1
            except PermissionRequired as pr:
                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("hera.auto_answer_pending_queries query %s: %s", query.pk, exc)

    logger.info("hera.auto_answer_pending_queries: answered %d queries", answered)
    return answered


@shared_task(name="agents.hera.weekly_onboarding_status")
def weekly_onboarding_status():
    from agents.hera.models import OnboardingTask
    from django.db.models import Count

    stats = (OnboardingTask.objects
             .values("business_id", "is_completed")
             .annotate(count=Count("id")))
    logger.info("hera.weekly_onboarding_status: %d stat rows", len(stats))
    return list(stats)


# ── P3C live task: uses hub HR data via LangChain ────────────────────────────

@shared_task(name="agents.hera.live_hr_check")
def live_hr_check():
    """Weekly HR check using live hub data — reads modules/hr/ via LangChain tools."""
    from agents.models import AgentInstance, AgentCatalog
    from agents.scheduled import run_scheduled_agent_task

    try:
        catalog = AgentCatalog.objects.get(slug='hera')
    except AgentCatalog.DoesNotExist:
        return 0

    count = 0
    for instance in (
        AgentInstance.objects
        .filter(catalog=catalog, status='idle')
        .select_related('business', 'catalog')
    ):
        run_scheduled_agent_task(
            instance=instance,
            task_name='live_hr_check',
            task_prompt=(
                "Perform your weekly HR health check using your data tools.\n"
                "1. Get headcount by department — flag any that seem understaffed.\n"
                "2. List all pending leave requests that need approval.\n"
                "3. Check for any employees with upcoming performance reviews due.\n"
                "Provide a concise HR status report with clear recommended actions."
            ),
        )
        count += 1
    logger.info("hera.live_hr_check: ran for %d businesses", count)
    return count
