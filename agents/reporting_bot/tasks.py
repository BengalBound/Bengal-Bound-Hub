import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.reporting_bot.scheduled_report_generation")
def scheduled_report_generation():
    from django.utils import timezone
    from datetime import timedelta
    from agents.reporting_bot.models import ReportConfig, Report
    from agents.reporting_bot.engine import ReportingBotEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='reporting_bot')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = ReportingBotEngine()
    today = timezone.now()
    generated = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        for config in ReportConfig.objects.filter(business=instance.business, is_active=True):
            should_run = False
            if config.frequency == "weekly" and config.send_day.lower() == today.strftime("%A").lower():
                should_run = True
            elif config.frequency == "monthly" and today.day == 1:
                should_run = True

            if not should_run:
                continue

            try:
                period_end = today.date()
                period_start = period_end - timedelta(weeks=1) if config.frequency == "weekly" else period_end.replace(day=1) - timedelta(days=1)

                report = Report.objects.create(
                    business=config.business,
                    config=config,
                    period_start=period_start,
                    period_end=period_end,
                    status="generating",
                )
                narrative = engine.generate_narrative(report, config, instance=instance)
                report.ai_narrative = narrative
                report.status = "ready"
                report.generated_at = timezone.now()
                report.save(update_fields=["ai_narrative", "status", "generated_at"])
                generated += 1
            except PermissionRequired as pr:
                if "narrative" in locals():
                    report.ai_narrative = narrative
                report.status = "waiting_approval"
                report.save(update_fields=["ai_narrative", "status"])

                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("reporting_bot.scheduled_report_generation config %s: %s", config.pk, exc)

    logger.info("reporting_bot.scheduled_report_generation: generated %d reports", generated)
    return generated


@shared_task(name="agents.reporting_bot.deliver_ready_reports")
def deliver_ready_reports():
    from django.utils import timezone
    from agents.reporting_bot.models import Report

    ready = Report.objects.filter(status="ready")
    delivered = 0

    for report in ready:
        recipients = report.config.recipients or []
        if recipients:
            logger.info("Reporting Bot: delivering report '%s' to %d recipients",
                        report.config.report_name, len(recipients))
            report.status = "sent"
            report.sent_at = timezone.now()
            report.save(update_fields=["status", "sent_at"])
            delivered += 1

    logger.info("reporting_bot.deliver_ready_reports: delivered %d reports", delivered)
    return delivered
