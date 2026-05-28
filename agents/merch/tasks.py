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
    from agents.merch.engine import MerchEngine

    engine = MerchEngine()
    unoptimised = Product.objects.filter(ai_description="").select_related("store")[:50]
    optimised = 0

    for product in unoptimised:
        try:
            result = engine.optimise_listing(product)
            product.ai_description = result.get("ai_description", "")
            if result.get("ai_price"):
                product.ai_price = result["ai_price"]
            product.save(update_fields=["ai_description", "ai_price"])
            optimised += 1
        except Exception as exc:
            logger.error("merch.daily_listing_optimisation product %s: %s", product.pk, exc)

    logger.info("merch.daily_listing_optimisation: optimised %d listings", optimised)
    return optimised


@shared_task(name="agents.merch.reorder_check")
def reorder_check():
    from agents.merch.models import Product
    from agents.merch.engine import MerchEngine

    engine = MerchEngine()
    critical = Product.objects.filter(is_low_stock=True).select_related("store")
    flagged = 0

    for product in critical:
        try:
            rec = engine.reorder_recommendation(product)
            if rec.get("urgency") in ["high", "critical"]:
                logger.warning("Merch reorder: %s — %s (stock: %d, urgency: %s)",
                               product.title, product.store.store_name,
                               product.stock_quantity, rec["urgency"])
                flagged += 1
        except Exception as exc:
            logger.error("merch.reorder_check product %s: %s", product.pk, exc)

    logger.info("merch.reorder_check: %d products need urgent reorder", flagged)
    return flagged
