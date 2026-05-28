import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.realt.qualify_new_leads")
def qualify_new_leads():
    from agents.realt.models import Lead
    from agents.realt.engine import RealtEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='realt')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = RealtEngine()
    qualified = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        new_leads = Lead.objects.filter(business=instance.business, status="new", ai_score__isnull=True)
        for lead in new_leads:
            try:
                result = engine.qualify_lead(lead, instance=instance)
                lead.ai_score = result.get("ai_score", 50)
                lead.ai_notes = result.get("ai_notes", "")
                lead.status = "qualified"
                lead.save(update_fields=["ai_score", "ai_notes", "status"])
                qualified += 1
            except PermissionRequired as pr:
                if "result" in locals():
                    lead.ai_score = result.get("ai_score", 50)
                lead.status = "waiting"
                lead.save(update_fields=["ai_score", "status"])

                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("realt.qualify_new_leads lead %s: %s", lead.pk, exc)

    logger.info("realt.qualify_new_leads: qualified %d leads", qualified)
    return qualified


@shared_task(name="agents.realt.optimise_new_listings")
def optimise_new_listings():
    from agents.realt.models import Property
    from agents.realt.engine import RealtEngine
    from agents.models import AgentInstance, AgentCatalog

    try:
        catalog = AgentCatalog.objects.get(slug='realt')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = RealtEngine()
    optimised = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        unlisted = Property.objects.filter(business=instance.business, ai_description="", status="available")
        for prop in unlisted:
            try:
                prop.ai_description = engine.generate_listing(prop, instance=instance)
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
    from agents.models import AgentInstance, AgentCatalog

    try:
        catalog = AgentCatalog.objects.get(slug='realt')
    except AgentCatalog.DoesNotExist:
        return 0

    cutoff = timezone.now() - timedelta(days=5)
    total_count = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        stale = Lead.objects.filter(business=instance.business, status__in=["new", "qualified"], created_at__lt=cutoff)
        count = stale.count()
        total_count += count
        if count > 0:
            logger.warning("realt.stale_lead_follow_up: %d leads stale >5 days for %s", count, instance.business.slug)
    return total_count
