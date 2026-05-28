from agents.models import AgentInstance

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Reporting Bot."""
    # Webhook support for ad-hoc reports
    pass
