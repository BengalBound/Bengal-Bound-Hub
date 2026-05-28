from agents.realt.engine import RealtEngine, PermissionRequired
from agents.realt.models import Lead
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Realt."""
    engine = RealtEngine()

    if event_type == 'lead_received':
        lead = Lead.objects.create(
            business=instance.business,
            name=payload.get('name', 'Unknown'),
            intent=payload.get('intent', 'buy'),
            budget_max=payload.get('budget_max', None),
            status='new'
        )

        try:
            result = engine.qualify_lead(lead, instance=instance)
            lead.ai_score = result.get("ai_score", 50)
            lead.ai_notes = result.get("ai_notes", "")
            lead.status = "qualified"
            lead.save(update_fields=["ai_score", "ai_notes", "status"])
        except PermissionRequired as pr:
            if "result" in locals():
                lead.ai_score = result.get("ai_score", 50)
            lead.status = "waiting"
            lead.save(update_fields=["ai_score", "status"])

            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
