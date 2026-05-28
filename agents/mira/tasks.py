import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.mira.at_risk_customer_alert")
def at_risk_customer_alert():
    from agents.mira.models import ClientHealth
    from agents.mira.engine import MiraEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='mira')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = MiraEngine()
    alerted = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        at_risk = ClientHealth.objects.filter(business=instance.business, risk_level__in=["at_risk", "critical"])
        for health in at_risk:
            try:
                result = engine.health_assessment(health, instance=instance)
                health.ai_summary = result.get("assessment", "")
                health.save(update_fields=["ai_summary"])
                logger.warning("Mira: at-risk customer (business %s) — churn risk: %s",
                               health.business_id, result.get("churn_risk", "unknown"))
                alerted += 1
            except PermissionRequired as pr:
                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("mira.at_risk_customer_alert health %s: %s", health.pk, exc)

    logger.info("mira.at_risk_customer_alert: alerted %d at-risk customers", alerted)
    return alerted


@shared_task(name="agents.mira.generate_pending_emails")
def generate_pending_emails():
    from agents.mira.models import SuccessEmail
    from agents.mira.engine import MiraEngine
    from agents.models import AgentInstance, AgentCatalog

    try:
        catalog = AgentCatalog.objects.get(slug='mira')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = MiraEngine()
    unsent_types = ["onboarding", "checkin"]
    generated = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        emails = SuccessEmail.objects.filter(business=instance.business, sent=False, body="")
        for email in emails:
            try:
                result = engine.draft_email(
                    business_name=str(email.business_id),
                    email_type=email.email_type,
                    instance=instance
                )
                email.subject = result.get("subject", email.subject)
                email.body = result.get("body", "")
                email.save(update_fields=["subject", "body"])
                generated += 1
            except Exception as exc:
                logger.error("mira.generate_pending_emails email %s: %s", email.pk, exc)

    logger.info("mira.generate_pending_emails: generated %d emails", generated)
    return generated


@shared_task(name="agents.mira.weekly_health_digest")
def weekly_health_digest():
    from agents.mira.models import ClientHealth
    from django.db.models import Count, Avg

    stats = {
        "by_risk": dict(ClientHealth.objects.values_list("risk_level").annotate(count=Count("id"))),
        "avg_health_score": ClientHealth.objects.aggregate(avg=Avg("health_score"))["avg"] or 0,
        "critical_count": ClientHealth.objects.filter(risk_level="critical").count(),
    }
    logger.info("mira.weekly_health_digest: %s", stats)
    return stats
