import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.tempo.event_reminder_dispatch")
def event_reminder_dispatch():
    from django.utils import timezone
    from datetime import timedelta
    from agents.tempo.models import Event, Attendee
    from agents.tempo.engine import TempoEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='tempo')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = TempoEngine()
    now = timezone.now()
    dispatched = 0

    two_weeks = now + timedelta(weeks=2)
    tomorrow = now + timedelta(days=1)

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        events_2wk = Event.objects.filter(business=instance.business, status__in=["planning", "confirmed"], date__date=two_weeks.date())
        for event in events_2wk:
            attendees = Attendee.objects.filter(event=event, rsvp_status="confirmed")
            try:
                message = engine.attendee_message(event, "reminder_2week", attendees.count(), instance=instance)
                logger.info("Tempo: 2-week reminder drafted for '%s'", event.name)
                dispatched += 1
            except PermissionRequired as pr:
                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("tempo.event_reminder_dispatch event %s (2wk): %s", event.pk, exc)
                
        events_1day = Event.objects.filter(business=instance.business, status__in=["planning", "confirmed"], date__date=tomorrow.date())
        for event in events_1day:
            attendees = Attendee.objects.filter(event=event, rsvp_status="confirmed")
            try:
                message = engine.attendee_message(event, "reminder_1day", attendees.count(), instance=instance)
                logger.info("Tempo: day-before reminder drafted for '%s'", event.name)
                dispatched += 1
            except PermissionRequired as pr:
                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("tempo.event_reminder_dispatch event %s (1day): %s", event.pk, exc)

    logger.info("tempo.event_reminder_dispatch: dispatched %d reminders", dispatched)
    return dispatched




@shared_task(name="agents.tempo.auto_generate_event_plans")
def auto_generate_event_plans():
    from agents.tempo.models import Event
    from agents.tempo.engine import TempoEngine
    from agents.models import AgentInstance, AgentCatalog

    try:
        catalog = AgentCatalog.objects.get(slug='tempo')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = TempoEngine()
    generated = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        without_plan = Event.objects.filter(business=instance.business, ai_plan="", status__in=["planning", "confirmed"])
        for event in without_plan:
            try:
                event.ai_plan = engine.generate_event_plan(event, instance=instance)
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
