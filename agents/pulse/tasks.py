import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.pulse.weekly_market_scan")
def weekly_market_scan():
    from django.utils import timezone
    from agents.pulse.models import ResearchConfig, ResearchReport
    from agents.pulse.engine import PulseEngine

    engine = PulseEngine()
    configs = ResearchConfig.objects.all()
    generated = 0

    for config in configs:
        try:
            period = timezone.now().strftime("%Y-W%U")
            report = ResearchReport.objects.create(
                business=config.business,
                period=period,
            )
            result = engine.generate_report(config, report)
            report.narrative = result.get("narrative", "")
            report.key_findings = result.get("key_findings", [])
            report.opportunities = result.get("opportunities", [])
            report.threats = result.get("threats", [])
            report.recommendations = result.get("recommendations", [])
            report.save()
            generated += 1
        except Exception as exc:
            logger.error("pulse.weekly_market_scan config %s: %s", config.pk, exc)

    logger.info("pulse.weekly_market_scan: generated %d reports", generated)
    return generated


@shared_task(name="agents.pulse.alert_threshold_check")
def alert_threshold_check():
    from agents.pulse.models import ResearchConfig, ResearchReport

    configs = ResearchConfig.objects.all()
    alerts = 0

    for config in configs:
        latest = ResearchReport.objects.filter(business=config.business).order_by("-generated_at").first()
        if not latest:
            continue
        high_threats = [t for t in (latest.threats or []) if t.get("probability") == "high" and t.get("impact") == "high"]
        if len(high_threats) >= 1:
            logger.warning("Pulse alert: %s has %d critical threats in latest report", config.business_id, len(high_threats))
            alerts += 1

    logger.info("pulse.alert_threshold_check: %d businesses with critical threats", alerts)
    return alerts
