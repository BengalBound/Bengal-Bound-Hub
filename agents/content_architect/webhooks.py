from agents.content_architect.engine import ContentArchitectEngine, PermissionRequired
from agents.content_architect.models import ContentCalendar
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Content Architect."""
    engine = ContentArchitectEngine()
    
    if event_type == 'calendar_requested':
        calendar, _ = ContentCalendar.objects.get_or_create(
            business=instance.business,
            name=payload.get('name', 'Monthly Content Plan'),
            month=payload.get('month', '2026-06'),
            defaults={
                'goal': payload.get('goal', 'Brand Awareness'),
                'status': 'draft'
            }
        )
        
        try:
            res = engine.plan_calendar(calendar, instance=instance)
            # normally we'd loop and create CalendarEntry objects from res here
            # for now, just marking it as planned if it succeeded without PermissionRequired
            calendar.status = 'planned'
            calendar.save(update_fields=['status'])
        except PermissionRequired as pr:
            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
