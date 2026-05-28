import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.payload.rfq_deadline_reminder")
def rfq_deadline_reminder():
    from django.utils import timezone
    from datetime import timedelta
    from agents.payload.models import RFQ
    from agents.models import AgentInstance, AgentCatalog

    try:
        catalog = AgentCatalog.objects.get(slug='payload')
    except AgentCatalog.DoesNotExist:
        return 0

    warning_window = timezone.now() + timedelta(days=2)
    total_count = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        expiring = RFQ.objects.filter(
            business=instance.business,
            status__in=["draft", "sent"],
            deadline__lte=warning_window,
            deadline__gte=timezone.now(),
        )
        count = expiring.count()
        total_count += count
        for rfq in expiring:
            logger.warning("Payload: RFQ '%s' deadline in <48h (%s) for %s", rfq.title, rfq.deadline, instance.business.slug)

    logger.info("payload.rfq_deadline_reminder: %d RFQs expiring soon", total_count)
    return total_count


@shared_task(name="agents.payload.auto_evaluate_completed_rfqs")
def auto_evaluate_completed_rfqs():
    from agents.payload.models import RFQ, Vendor
    from agents.payload.engine import PayloadEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='payload')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = PayloadEngine()
    evaluated = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        ready = RFQ.objects.filter(business=instance.business, status="responses_in", ai_recommendation="")
        for rfq in ready:
            try:
                vendors = list(Vendor.objects.filter(business=rfq.business, status="active"))
                if not vendors:
                    continue
                result = engine.evaluate_rfq(rfq, vendors, instance=instance)
                rfq.ai_recommendation = result.get("ai_recommendation", "")
                rfq.status = "evaluated"
                rfq.save(update_fields=["ai_recommendation", "status"])
                evaluated += 1
            except PermissionRequired as pr:
                if "result" in locals():
                    rfq.ai_recommendation = result.get("ai_recommendation", "")
                rfq.status = "waiting_approval"
                rfq.save(update_fields=["ai_recommendation", "status"])

                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("payload.auto_evaluate_completed_rfqs rfq %s: %s", rfq.pk, exc)

    logger.info("payload.auto_evaluate_completed_rfqs: evaluated %d RFQs", evaluated)
    return evaluated


@shared_task(name="agents.payload.vendor_performance_review")
def vendor_performance_review():
    from agents.payload.models import Vendor
    from agents.payload.engine import PayloadEngine
    from agents.models import AgentInstance, AgentCatalog

    try:
        catalog = AgentCatalog.objects.get(slug='payload')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = PayloadEngine()
    reviewed = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        at_risk = Vendor.objects.filter(
            business=instance.business,
            performance_score__isnull=False,
            performance_score__lt=60,
            status="active",
        )
        for vendor in at_risk:
            try:
                result = engine.assess_vendor(vendor, instance=instance)
                if result.get("status_recommendation") in ["on_hold", "blacklisted"]:
                    vendor.status = result["status_recommendation"]
                    vendor.save(update_fields=["status"])
                    logger.warning("Payload: vendor %s → status changed to %s for %s", vendor.name, vendor.status, instance.business.slug)
                reviewed += 1
            except Exception as exc:
                logger.error("payload.vendor_performance_review vendor %s: %s", vendor.pk, exc)

    logger.info("payload.vendor_performance_review: reviewed %d at-risk vendors", reviewed)
    return reviewed
