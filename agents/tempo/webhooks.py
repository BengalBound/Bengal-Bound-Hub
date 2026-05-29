from django.utils import timezone
import dateutil.parser
from agents.tempo.engine import TempoEngine
from agents.tempo.models import Event
from agents.models import AgentInstance

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Tempo."""
    engine = TempoEngine()

    if event_type == 'calendly_invitee_created' or event_type == 'calendar_booking':
        # Create event from webhook payload
        try:
            event_date = dateutil.parser.isoparse(payload.get('start_time'))
        except (ValueError, TypeError):
            event_date = timezone.now()

        event, created = Event.objects.get_or_create(
            business=instance.business,
            name=payload.get('event_name', 'New Booking'),
            date=event_date,
            defaults={
                'event_type': 'workshop',
                'location': payload.get('location', 'Online'),
                'expected_headcount': 1,
                'status': 'planning'
            }
        )

        if created and not event.ai_plan:
            event.ai_plan = engine.generate_event_plan(event, instance=instance)
            event.save(update_fields=['ai_plan'])
