from agents.serea_content.models import Campaign
from agents.models import AgentInstance

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Serea Content."""

    if event_type == 'campaign_requested':
        Campaign.objects.create(
            business=instance.business,
            name=payload.get('name', 'New Campaign'),
            goal=payload.get('goal', ''),
            status='active'
        )
        # The campaign_strategy_generation task will pick this up
