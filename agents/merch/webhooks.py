from agents.merch.engine import MerchEngine, PermissionRequired
from agents.merch.models import Product, ConnectedStore
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Merch."""
    engine = MerchEngine()

    if event_type == 'inventory_level.updated':
        # E.g., Shopify inventory webhook
        store, _ = ConnectedStore.objects.get_or_create(
            business=instance.business,
            store_url=payload.get('store_url', ''),
            defaults={'platform': payload.get('platform', 'shopify'), 'store_name': payload.get('store_name', 'Unknown Store')}
        )
        product, _ = Product.objects.get_or_create(
            store=store,
            sku=payload.get('sku', ''),
            defaults={
                'title': payload.get('title', 'Unknown Product'),
                'price': payload.get('price', 0.00),
                'stock_quantity': payload.get('available', 0),
                'reorder_threshold': 10
            }
        )
        product.stock_quantity = payload.get('available', 0)

        if product.stock_quantity <= product.reorder_threshold:
            product.is_low_stock = True
            try:
                engine.reorder_recommendation(product, instance=instance)
            except PermissionRequired as pr:
                AgentPermissionRequest.objects.create(
                    instance=instance,
                    context=pr.context,
                    option_a=pr.option_a,
                    option_b=pr.option_b,
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])

        product.save(update_fields=['stock_quantity', 'is_low_stock'])
