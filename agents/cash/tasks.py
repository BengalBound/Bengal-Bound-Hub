import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.cash.monthly_payroll_reminder")
def monthly_payroll_reminder():
    from django.utils import timezone
    from agents.cash.models import PayrollRun
    from hub.models import BusinessInstance

    today = timezone.now()
    # Remind on the 25th of each month
    if today.day != 25:
        return "not payroll reminder day"

    businesses_without_run = []
    current_month = today.replace(day=1).date()

    for business in BusinessInstance.objects.filter(is_active=True):
        has_run = PayrollRun.objects.filter(business=business, month=current_month).exists()
        if not has_run:
            businesses_without_run.append(business.slug)
            logger.warning("Cash: no payroll run for %s in %s", business.slug, current_month)

    logger.info("cash.monthly_payroll_reminder: %d businesses missing runs", len(businesses_without_run))
    return businesses_without_run


@shared_task(name="agents.cash.anomaly_check_all")
def anomaly_check_all():
    from agents.cash.models import PayrollRun
    from agents.cash.engine import CashEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='cash')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = CashEngine()
    flagged = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        recent_runs = PayrollRun.objects.filter(business=instance.business, status="draft").select_related("business")
        for run in recent_runs:
            try:
                previous = (PayrollRun.objects.filter(business=run.business, status__in=["approved", "transferred"])
                            .order_by("-month").first())
                if previous:
                    anomalies = engine.anomaly_check(run, {
                        "month": str(previous.month),
                        "total_gross": float(previous.total_gross),
                        "employee_count": previous.employee_count,
                    }, instance=instance)
                    if anomalies:
                        logger.warning("Cash anomalies in run %s: %s", run.pk, anomalies)
                        flagged += 1
            except PermissionRequired as pr:
                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("cash.anomaly_check run %s: %s", run.pk, exc)

    logger.info("cash.anomaly_check_all: %d runs flagged", flagged)
    return flagged


# ── P3C live task: uses hub Invoice data via LangChain ───────────────────────

@shared_task(name="agents.cash.live_invoice_review")
def live_invoice_review():
    """Weekly cash flow review using live hub data — reads modules/invoicing/ via LangChain tools."""
    from agents.models import AgentInstance, AgentCatalog
    from agents.scheduled import run_scheduled_agent_task

    try:
        catalog = AgentCatalog.objects.get(slug='cash')
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
            task_name='live_invoice_review',
            task_prompt=(
                "Perform your weekly cash flow review using your data tools.\n"
                "1. Get the revenue summary — total invoiced, collected, and outstanding balance.\n"
                "2. List any overdue invoices and identify clients who owe the most.\n"
                "3. Recommend specific follow-up actions for the top 3 overdue accounts.\n"
                "Provide a concise cash flow briefing with urgency-ranked action items."
            ),
        )
        count += 1
    logger.info("cash.live_invoice_review: ran for %d businesses", count)
    return count
