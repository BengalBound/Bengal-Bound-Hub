from agents.shield.engine import ShieldEngine, PermissionRequired
from agents.shield.models import ITTicket
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Shield."""
    engine = ShieldEngine()
    
    if event_type == 'ticket_created':
        ticket, created = ITTicket.objects.get_or_create(
            business=instance.business,
            title=payload.get('title', 'Unknown Issue'),
            defaults={
                'category': payload.get('category', 'other'),
                'description': payload.get('description', ''),
                'priority': payload.get('priority', 'medium'),
                'submitted_by': payload.get('submitted_by', 'Unknown User'),
                'status': 'open'
            }
        )
        
        if created:
            try:
                # Shield tries to resolve on ticket creation immediately
                res = engine.resolve_ticket(ticket, [], instance=instance)
                
                ticket.ai_solution = res.get("ai_solution", "")
                ticket.ai_confidence = res.get("ai_confidence", 0.5)
                ticket.sla_hours = {"low": 48, "medium": 24, "high": 4, "urgent": 1}.get(ticket.priority, 24)

                if res.get("should_auto_resolve") and res.get("ai_confidence", 0) >= 0.8:
                    ticket.status = "resolved"
                else:
                    ticket.status = "ai_resolving"
                ticket.save(update_fields=["ai_solution", "ai_confidence", "sla_hours", "status"])
            except PermissionRequired as pr:
                if "res" in locals():
                    ticket.ai_solution = res.get("ai_solution", "")
                    ticket.ai_confidence = res.get("ai_confidence", 0.5)
                    ticket.sla_hours = {"low": 48, "medium": 24, "high": 4, "urgent": 1}.get(ticket.priority, 24)
                    ticket.status = "ai_resolving"
                    ticket.save(update_fields=["ai_solution", "ai_confidence", "sla_hours", "status"])
                
                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
