import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.flux.overdue_po_alert")
def overdue_po_alert():
    from django.utils import timezone
    from agents.flux.models import PurchaseOrder

    today = timezone.now().date()
    overdue = PurchaseOrder.objects.filter(
        status__in=["sent", "confirmed", "shipped"],
        expected_date__lt=today,
    )
    count = overdue.count()
    overdue.update(status="overdue")
    logger.warning("flux.overdue_po_alert: %d POs marked overdue", count)
    return count


@shared_task(name="agents.flux.supplier_performance_review")
def supplier_performance_review():
    from agents.flux.models import Supplier
    from agents.flux.engine import FluxEngine

    engine = FluxEngine()
    suppliers = Supplier.objects.filter(rating__in=["average", "poor"])
    reviewed = 0

    for supplier in suppliers:
        try:
            result = engine.assess_supplier(supplier)
            supplier.ai_summary = result.get("ai_summary", "")
            supplier.rating = result.get("rating", supplier.rating)
            supplier.save(update_fields=["ai_summary", "rating"])
            reviewed += 1
        except Exception as exc:
            logger.error("flux.supplier_performance_review supplier %s: %s", supplier.pk, exc)

    logger.info("flux.supplier_performance_review: reviewed %d suppliers", reviewed)
    return reviewed
