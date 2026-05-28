import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.payload.rfq_deadline_reminder")
def rfq_deadline_reminder():
    from django.utils import timezone
    from datetime import timedelta
    from agents.payload.models import RFQ

    warning_window = timezone.now() + timedelta(days=2)
    expiring = RFQ.objects.filter(
        status__in=["draft", "sent"],
        deadline__lte=warning_window,
        deadline__gte=timezone.now(),
    )
    count = expiring.count()
    for rfq in expiring:
        logger.warning("Payload: RFQ '%s' deadline in <48h (%s)", rfq.title, rfq.deadline)
    logger.info("payload.rfq_deadline_reminder: %d RFQs expiring soon", count)
    return count


@shared_task(name="agents.payload.auto_evaluate_completed_rfqs")
def auto_evaluate_completed_rfqs():
    from agents.payload.models import RFQ, Vendor
    from agents.payload.engine import PayloadEngine

    engine = PayloadEngine()
    ready = RFQ.objects.filter(status="responses_in", ai_recommendation="")
    evaluated = 0

    for rfq in ready:
        try:
            vendors = list(Vendor.objects.filter(business=rfq.business, status="active"))
            if not vendors:
                continue
            result = engine.evaluate_rfq(rfq, vendors)
            rfq.ai_recommendation = result.get("ai_recommendation", "")
            rfq.status = "evaluated"
            rfq.save(update_fields=["ai_recommendation", "status"])
            evaluated += 1
        except Exception as exc:
            logger.error("payload.auto_evaluate_completed_rfqs rfq %s: %s", rfq.pk, exc)

    logger.info("payload.auto_evaluate_completed_rfqs: evaluated %d RFQs", evaluated)
    return evaluated


@shared_task(name="agents.payload.vendor_performance_review")
def vendor_performance_review():
    from agents.payload.models import Vendor
    from agents.payload.engine import PayloadEngine

    engine = PayloadEngine()
    at_risk = Vendor.objects.filter(
        performance_score__isnull=False,
        performance_score__lt=60,
        status="active",
    )
    reviewed = 0

    for vendor in at_risk:
        try:
            result = engine.assess_vendor(vendor)
            if result.get("status_recommendation") in ["on_hold", "blacklisted"]:
                vendor.status = result["status_recommendation"]
                vendor.save(update_fields=["status"])
                logger.warning("Payload: vendor %s → status changed to %s", vendor.name, vendor.status)
            reviewed += 1
        except Exception as exc:
            logger.error("payload.vendor_performance_review vendor %s: %s", vendor.pk, exc)

    logger.info("payload.vendor_performance_review: reviewed %d at-risk vendors", reviewed)
    return reviewed
