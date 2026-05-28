from agents.lead_hunter.engine import LeadHunterEngine, PermissionRequired
from agents.lead_hunter.models import Prospect
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Lead Hunter."""
    engine = LeadHunterEngine()
    
    if event_type == 'prospect_added':
        prospect, _ = Prospect.objects.get_or_create(
            business=instance.business,
            company_name=payload.get('company_name', ''),
            contact_name=payload.get('contact_name', ''),
            defaults={
                'industry': payload.get('industry', ''),
                'linkedin_url': payload.get('linkedin_url', ''),
                'notes': payload.get('notes', ''),
                'status': 'new',
            }
        )
        
        try:
            # Auto-score new prospect
            result = engine.score_prospect(prospect, instance=instance)
            prospect.score = result.get("score", 50)
            prospect.ai_summary = result.get("ai_summary", "")
            prospect.save(update_fields=["score", "ai_summary"])
        except PermissionRequired as pr:
            if "result" in locals():
                prospect.score = result.get("score", 50)
                prospect.ai_summary = result.get("ai_summary", "")
                prospect.save(update_fields=["score", "ai_summary"])
                
            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
