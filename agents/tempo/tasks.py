import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.tempo.event_reminder_dispatch")
def event_reminder_dispatch():
    from django.utils import timezone
    from datetime import timedelta
    from agents.tempo.models import Event, Attendee
    from agents.tempo.engine import TempoEngine

    engine = TempoEngine()
    now = timezone.now()
    dispatched = 0

    # 2-week reminders
    two_weeks = now + timedelta(weeks=2)
    for event in Event.objects.filter(status__in=["planning", "confirmed"],
                                       date__date=two_weeks.date()):
        attendees = Attendee.objects.filter(event=event, rsvp_status="confirmed")
        try:
            message = engine.attendee_message(event, "reminder_2week", attendees.count())
            logger.info("Tempo: 2-week reminder drafted for '%s' (%d attendees)", event.name, attendees.count())
            dispatched += 1
        except Exception as exc:
            logger.error("tempo.event_reminder_dispatch event %s (2wk): %s", event.pk, exc)

    # Day-before reminders
    tomorrow = now + timedelta(days=1)
    for event in Event.objects.filter(status__in=["planning", "confirmed"],
                                       date__date=tomorrow.date()):
        attendees = Attendee.objects.filter(event=event, rsvp_status="confirmed")
        try:
            message = engine.attendee_message(event, "reminder_1day", attendees.count())
            logger.info("Tempo: day-before reminder drafted for '%s'", event.name)
            dispatched += 1
        except Exception as exc:
            logger.error("tempo.event_reminder_dispatch event %s (1day): %s", event.pk, exc)

    logger.info("tempo.event_reminder_dispatch: dispatched %d reminders", dispatched)
    return dispatched


@shared_task(name="agents.tempo.auto_generate_event_plans")
def auto_generate_event_plans():
    from agents.tempo.models import Event
    from agents.tempo.engine import TempoEngine

    engine = TempoEngine()
    without_plan = Event.objects.filter(ai_plan="", status__in=["planning", "confirmed"])
    generated = 0

    for event in without_plan:
        try:
            event.ai_plan = engine.generate_event_plan(event)
            event.save(update_fields=["ai_plan"])
            generated += 1
        except Exception as exc:
            logger.error("tempo.auto_generate_event_plans event %s: %s", event.pk, exc)

    logger.info("tempo.auto_generate_event_plans: generated %d plans", generated)
    return generated


@shared_task(name="agents.tempo.rsvp_followup")
def rsvp_followup():
    from django.utils import timezone
    from datetime import timedelta
    from agents.tempo.models import Attendee

    cutoff = timezone.now() + timedelta(weeks=1)
    pending = Attendee.objects.filter(
        rsvp_status="pending",
        event__date__lte=cutoff,
    )
    count = pending.count()
    logger.warning("tempo.rsvp_followup: %d pending RSVPs need follow-up (event within 1 week)", count)
    return count
