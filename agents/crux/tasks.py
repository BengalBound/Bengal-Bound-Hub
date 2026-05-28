import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.crux.daily_pipeline_review")
def daily_pipeline_review():
    from agents.crux.models import Contact
    from agents.crux.engine import CruxEngine
    from hub.models import BusinessInstance

    engine = CruxEngine()
    processed = 0

    for business in BusinessInstance.objects.filter(is_active=True):
        contacts = list(Contact.objects.filter(business=business))
        if not contacts:
            continue
        try:
            report = engine.pipeline_health_report(contacts)
            logger.info("Crux pipeline report for %s generated", business.slug)
            processed += 1
        except Exception as exc:
            logger.error("crux.daily_pipeline_review business %s: %s", business.slug, exc)

    logger.info("crux.daily_pipeline_review: processed %d businesses", processed)
    return processed


@shared_task(name="agents.crux.score_new_contacts")
def score_new_contacts():
    from agents.crux.models import Contact, Interaction
    from agents.crux.engine import CruxEngine

    engine = CruxEngine()
    unscored = Contact.objects.filter(intent_score__isnull=True)
    scored = 0

    for contact in unscored:
        try:
            interactions = list(contact.interactions.order_by("-occurred_at")[:10])
            result = engine.score_contact(contact, interactions)
            contact.intent_score = result.get("intent_score", 50)
            contact.ai_summary = result.get("ai_summary", "")
            contact.save(update_fields=["intent_score", "ai_summary"])
            scored += 1
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
