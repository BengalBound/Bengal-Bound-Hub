import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.medibook.send_appointment_reminders")
def send_appointment_reminders():
    from django.utils import timezone
    from datetime import timedelta
    from agents.medibook.models import Appointment
    from agents.medibook.engine import MediBookEngine

    engine = MediBookEngine()
    window_start = timezone.now() + timedelta(hours=23)
    window_end = timezone.now() + timedelta(hours=25)

    due = Appointment.objects.filter(
        status__in=["booked", "confirmed"],
        scheduled_at__range=[window_start, window_end],
        reminder_sent=False,
    )
    sent = 0

    for appt in due:
        try:
            reminder = engine.reminder_message(appt, hours_before=24)
            logger.info("MediBook reminder: %s for %s at %s",
                        appt.patient_name, appt.doctor.name, appt.scheduled_at)
            appt.reminder_sent = True
            appt.save(update_fields=["reminder_sent"])
            sent += 1
        except Exception as exc:
            logger.error("medibook.send_appointment_reminders appt %s: %s", appt.pk, exc)

    logger.info("medibook.send_appointment_reminders: sent %d reminders", sent)
    return sent


@shared_task(name="agents.medibook.no_show_followup")
def no_show_followup():
    from django.utils import timezone
    from agents.medibook.models import Appointment

    past = timezone.now()
    no_shows = Appointment.objects.filter(
        scheduled_at__lt=past,
        status__in=["booked", "confirmed"],
    )
    count = no_shows.count()
    no_shows.update(status="no_show")
    logger.warning("medibook.no_show_followup: marked %d as no-show", count)
    return count


@shared_task(name="agents.medibook.generate_missing_notes")
def generate_missing_notes():
    from agents.medibook.models import Appointment
    from agents.medibook.engine import MediBookEngine

    engine = MediBookEngine()
    missing = Appointment.objects.filter(ai_notes="", status__in=["booked", "confirmed"])
    generated = 0

    for appt in missing:
        try:
            appt.ai_notes = engine.generate_appointment_notes(appt)
            appt.save(update_fields=["ai_notes"])
            generated += 1
        except Exception as exc:
            logger.error("medibook.generate_missing_notes appt %s: %s", appt.pk, exc)

    logger.info("medibook.generate_missing_notes: generated %d notes", generated)
    return generated
