import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.crux.daily_pipeline_review")
def daily_pipeline_review():
    from agents.crux.models import Contact
    from agents.crux.engine import CruxEngine
    from agents.models import AgentInstance, AgentCatalog

    try:
        catalog = AgentCatalog.objects.get(slug='crux')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = CruxEngine()
    processed = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        contacts = list(Contact.objects.filter(business=instance.business))
        if not contacts:
            continue
        try:
            report = engine.pipeline_health_report(contacts, instance=instance)
            logger.info("Crux pipeline report for %s generated", instance.business.slug)
            processed += 1
        except Exception as exc:
            logger.error("crux.daily_pipeline_review business %s: %s", instance.business.slug, exc)

    logger.info("crux.daily_pipeline_review: processed %d businesses", processed)
    return processed


@shared_task(name="agents.crux.score_new_contacts")
def score_new_contacts():
    from agents.crux.models import Contact
    from agents.crux.engine import CruxEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='crux')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = CruxEngine()
    scored = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        unscored = Contact.objects.filter(business=instance.business, intent_score__isnull=True)
        for contact in unscored:
            try:
                interactions = list(contact.interactions.order_by("-occurred_at")[:10])
                result = engine.score_contact(contact, interactions, instance=instance)
                contact.intent_score = result.get("intent_score", 50)
                contact.ai_summary = result.get("ai_summary", "")
                contact.save(update_fields=["intent_score", "ai_summary"])
                scored += 1
            except PermissionRequired as pr:
                if "result" in locals():
                    contact.intent_score = locals()['result'].get("intent_score", 50)
                    contact.ai_summary = locals()['result'].get("ai_summary", "")
                    contact.save(update_fields=["intent_score", "ai_summary"])

                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("crux.score_new_contacts contact %s: %s", contact.pk, exc)

    logger.info("crux.score_new_contacts: scored %d contacts", scored)
    return scored


@shared_task(name="agents.crux.dormant_contact_alert")
def dormant_contact_alert():
    from django.utils import timezone
    from datetime import timedelta
    from agents.crux.models import Contact

    cutoff = timezone.now() - timedelta(days=7)
    dormant = Contact.objects.filter(
        last_activity__lt=cutoff,
        is_cold=False,
        pipeline_stage__in=["qualified", "proposal", "negotiation"],
    )
    count = dormant.count()
    dormant.update(is_cold=True)
    logger.warning("crux.dormant_contact_alert: marked %d contacts as cold", count)
    return count
