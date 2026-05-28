from agents.flux.engine import FluxEngine
from agents.flux.models import PurchaseOrder
from agents.models import AgentInstance

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Flux."""
    engine = FluxEngine()

    if event_type == 'po_created':
        # Assume PO already exists and just needs review
        po_number = payload.get('po_number')
        try:
            order = PurchaseOrder.objects.get(business=instance.business, po_number=po_number)
            engine.po_recommendation(order, instance=instance)
        except PurchaseOrder.DoesNotExist:
            pass
