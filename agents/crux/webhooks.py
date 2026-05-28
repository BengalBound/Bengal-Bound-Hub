from agents.crux.engine import CruxEngine, PermissionRequired
from agents.crux.models import Contact, Interaction
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Crux."""
    engine = CruxEngine()
    
    if event_type == 'contact_created':
        contact, _ = Contact.objects.get_or_create(
            business=instance.business,
            email=payload.get('email', ''),
            defaults={
                'name': payload.get('name', 'Unknown'),
                'company': payload.get('company', ''),
                'pipeline_stage': payload.get('pipeline_stage', 'prospect'),
            }
        )
        
        try:
            # Score it right away
            res = engine.score_contact(contact, [], instance=instance)
            contact.intent_score = res.get("intent_score", contact.intent_score)
            contact.ai_summary = res.get("ai_summary", contact.ai_summary)
            contact.save(update_fields=["intent_score", "ai_summary"])
        except PermissionRequired as pr:
            if "res" in locals():
                contact.intent_score = res.get("intent_score", contact.intent_score)
                contact.ai_summary = res.get("ai_summary", contact.ai_summary)
                contact.save(update_fields=["intent_score", "ai_summary"])
                
            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
