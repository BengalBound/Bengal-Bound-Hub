import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.merch.low_stock_alert")
def low_stock_alert():
    from agents.merch.models import Product
    from django.db.models import F

    count = Product.objects.filter(
        stock_quantity__lte=F("reorder_threshold"),
        is_low_stock=False,
    ).update(is_low_stock=True)
    logger.warning("merch.low_stock_alert: flagged %d low-stock products", count)
    return count


@shared_task(name="agents.merch.daily_listing_optimisation")
def daily_listing_optimisation():
    from agents.merch.models import Product
    from agents.merch.engine import MerchEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='merch')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = MerchEngine()
    optimised = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        unoptimised = Product.objects.filter(store__business=instance.business, ai_description="").select_related("store")[:50]
        for product in unoptimised:
            try:
                result = engine.optimise_listing(product, instance=instance)
                product.ai_description = result.get("ai_description", "")
                if result.get("ai_price") and float(result["ai_price"]) == float(product.price):
                    # No price change needed, or it was denied initially but we just updated description
                    pass
                product.save(update_fields=["ai_description"])
                optimised += 1
            except PermissionRequired as pr:
                # We save the description, but pend the price change
                if "ai_description" in locals().get('result', {}):
                    product.ai_description = locals()['result']["ai_description"]
                    product.save(update_fields=["ai_description"])
                
                AgentPermissionRequest.objects.create(
                    instance=instance,
                    context=pr.context,
                    option_a=pr.option_a,
                    option_b=pr.option_b,
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("merch.daily_listing_optimisation product %s: %s", product.pk, exc)

    logger.info("merch.daily_listing_optimisation: optimised %d listings", optimised)
    return optimised


@shared_task(name="agents.merch.reorder_check")
def reorder_check():
    from agents.merch.models import Product
    from agents.merch.engine import MerchEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='merch')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = MerchEngine()
    flagged = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        critical = Product.objects.filter(store__business=instance.business, is_low_stock=True).select_related("store")
        for product in critical:
            try:
                rec = engine.reorder_recommendation(product, instance=instance)
                if rec.get("urgency") in ["high", "critical"]:
                    logger.warning("Merch reorder: %s — %s (stock: %d, urgency: %s)",
                                   product.title, product.store.store_name,
                                   product.stock_quantity, rec["urgency"])
                    flagged += 1
            except PermissionRequired as pr:
                AgentPermissionRequest.objects.create(
                    instance=instance,
                    context=pr.context,
                    option_a=pr.option_a,
                    option_b=pr.option_b,
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("merch.reorder_check product %s: %s", product.pk, exc)

    logger.info("merch.reorder_check: %d products need urgent reorder", flagged)
    return flagged
