from agents.atlas.engine import AtlasEngine, PermissionRequired
from agents.atlas.models import MeetingBrief
from agents.models import AgentInstance, AgentPermissionRequest
from django.utils.dateparse import parse_datetime
from django.utils import timezone

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Atlas."""
    engine = AtlasEngine()
    
    if event_type == 'meeting_scheduled':
        scheduled_at_str = payload.get('scheduled_at')
        scheduled_at = parse_datetime(scheduled_at_str) if scheduled_at_str else timezone.now()
        
        meeting = MeetingBrief.objects.create(
            business=instance.business,
            meeting_title=payload.get('meeting_title', 'Meeting'),
            scheduled_at=scheduled_at,
            attendees=payload.get('attendees', []),
            agenda=payload.get('agenda', '')
        )
        
        try:
            result = engine.generate_briefing(meeting, instance=instance)
            meeting.ai_briefing = result.get("ai_briefing", "")
            meeting.save(update_fields=["ai_briefing"])
        except PermissionRequired as pr:
            if "result" in locals():
                meeting.ai_briefing = result.get("ai_briefing", "")
                meeting.save(update_fields=["ai_briefing"])
                
            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
