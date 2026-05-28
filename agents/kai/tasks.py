import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.kai.pipeline_health_monitor")
def pipeline_health_monitor():
    from agents.kai.models import Pipeline
    from agents.kai.engine import KaiEngine

    engine = KaiEngine()
    failing = Pipeline.objects.filter(last_status="failing")
    alerts = 0

    for pipeline in failing:
        try:
            result = engine.pipeline_health_check(pipeline)
            alert_level = result.get("alert_level", "none")
            if alert_level in ["warning", "critical"]:
                logger.warning("Kai: pipeline [%s] health score %d — %s",
                               pipeline.name, result.get("health_score", 0), alert_level)
                alerts += 1
        except Exception as exc:
            logger.error("kai.pipeline_health_monitor pipeline %s: %s", pipeline.pk, exc)

    logger.info("kai.pipeline_health_monitor: %d alerts raised", alerts)
    return alerts


@shared_task(name="agents.kai.auto_analyze_open_incidents")
def auto_analyze_open_incidents():
    from agents.kai.models import Incident
    from agents.kai.engine import KaiEngine

    engine = KaiEngine()
    open_incidents = Incident.objects.filter(status="open", ai_root_cause="")
    analyzed = 0

    for incident in open_incidents:
        try:
            result = engine.analyze_incident(incident)
            incident.ai_root_cause = result.get("root_cause", "")
            incident.status = "investigating"
            incident.save(update_fields=["ai_root_cause", "status"])
            analyzed += 1
        except Exception as exc:
            logger.error("kai.auto_analyze_open_incidents incident %s: %s", incident.pk, exc)

    logger.info("kai.auto_analyze_open_incidents: analyzed %d incidents", analyzed)
    return analyzed


@shared_task(name="agents.kai.daily_devops_digest")
def daily_devops_digest():
    from agents.kai.models import Pipeline, Incident
    from django.db.models import Count

    pipeline_stats = dict(Pipeline.objects.values_list("last_status").annotate(count=Count("id")))
    incident_stats = dict(Incident.objects.filter(status__in=["open", "investigating"])
                          .values_list("severity").annotate(count=Count("id")))

    logger.info("Kai daily digest — Pipelines: %s | Incidents: %s", pipeline_stats, incident_stats)
    return {"pipelines": pipeline_stats, "incidents": incident_stats}
