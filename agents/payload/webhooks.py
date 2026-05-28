from agents.payload.engine import PayloadEngine
from agents.models import AgentInstance

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Payload."""
    engine = PayloadEngine()

    if event_type == 'rfq_created':
        # Webhook creates an RFQ draft
        pass
