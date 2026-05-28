import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.realt.qualify_new_leads")
def qualify_new_leads():
    from agents.realt.models import Lead
    from agents.realt.engine import RealtEngine

    engine = RealtEngine()
    new_leads = Lead.objects.filter(status="new", ai_score__isnull=True)
    qualified = 0

    for lead in new_leads:
        try:
            result = engine.qualify_lead(lead)
            lead.ai_score = result.get("ai_score", 50)
            lead.ai_notes = result.get("ai_notes", "")
            lead.status = "qualified"
            lead.save(update_fields=["ai_score", "ai_notes", "status"])
            qualified += 1
        except Exception as exc:
            logger.error("realt.qualify_new_leads lead %s: %s", lead.pk, exc)

    logger.info("realt.qualify_new_leads: qualified %d leads", qualified)
    return qualified


@shared_task(name="agents.realt.optimise_new_listings")
def optimise_new_listings():
    from agents.realt.models import Property
    from agents.realt.engine import RealtEngine

    engine = RealtEngine()
    unlisted = Property.objects.filter(ai_description="", status="available")
    optimised = 0

    for prop in unlisted:
        try:
            prop.ai_description = engine.generate_listing(prop)
            prop.save(update_fields=["ai_description"])
            optimised += 1
        except Exception as exc:
            logger.error("realt.optimise_new_listings property %s: %s", prop.pk, exc)

    logger.info("realt.optimise_new_listings: optimised %d listings", optimised)
    return optimised


@shared_task(name="agents.realt.stale_lead_follow_up")
def stale_lead_follow_up():
    from django.utils import timezone
    from datetime import timedelta
    from agents.realt.models import Lead

    cutoff = timezone.now() - timedelta(days=5)
    stale = Lead.objects.filter(status__in=["new", "qualified"], created_at__lt=cutoff)
    count = stale.count()
    logger.warning("realt.stale_lead_follow_up: %d leads stale >5 days", count)
    return count
