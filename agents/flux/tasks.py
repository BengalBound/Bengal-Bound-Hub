import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.flux.overdue_po_alert")
def overdue_po_alert():
    from django.utils import timezone
    from agents.flux.models import PurchaseOrder
    from agents.models import AgentInstance, AgentCatalog

    try:
        catalog = AgentCatalog.objects.get(slug='flux')
    except AgentCatalog.DoesNotExist:
        return 0

    today = timezone.now().date()
    total_count = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        overdue = PurchaseOrder.objects.filter(
            business=instance.business,
            status__in=["sent", "confirmed", "shipped"],
            expected_date__lt=today,
        )
        count = overdue.update(status="overdue")
        total_count += count
        if count > 0:
            logger.warning("flux.overdue_po_alert: %d POs marked overdue for %s", count, instance.business.slug)

    return total_count


@shared_task(name="agents.flux.supplier_performance_review")
def supplier_performance_review():
    from agents.flux.models import Supplier
    from agents.flux.engine import FluxEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='flux')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = FluxEngine()
    reviewed = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        suppliers = Supplier.objects.filter(business=instance.business, rating__in=["average", "poor"])
        for supplier in suppliers:
            try:
                result = engine.assess_supplier(supplier, instance=instance)
                supplier.ai_summary = result.get("ai_summary", "")
                supplier.rating = result.get("rating", supplier.rating)
                supplier.save(update_fields=["ai_summary", "rating"])
                reviewed += 1
            except PermissionRequired as pr:
                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("flux.supplier_performance_review supplier %s: %s", supplier.pk, exc)

    logger.info("flux.supplier_performance_review: reviewed %d suppliers", reviewed)
    return reviewed
