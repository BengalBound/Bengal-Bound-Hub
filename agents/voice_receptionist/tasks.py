import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.voice_receptionist.send_appointment_reminders_24h")
def send_appointment_reminders_24h():
    from django.utils import timezone
    from datetime import timedelta
    from agents.voice_receptionist.models import Appointment, AppointmentStatus
    from agents.voice_receptionist.notifications import notify_appointment

    now = timezone.now()
    window_start = now + timedelta(hours=23, minutes=30)
    window_end = now + timedelta(hours=24, minutes=30)

    upcoming = Appointment.objects.filter(
        scheduled_at__gte=window_start,
        scheduled_at__lte=window_end,
        status=AppointmentStatus.CONFIRMED,
    ).select_related("business")

    sent = 0
    for appt in upcoming:
        try:
            notify_appointment(appt, "reminder_24h")
            sent += 1
        except Exception as exc:
            logger.error("voice_receptionist.24h_reminder appt %s: %s", appt.id, exc)

    logger.info("voice_receptionist.send_appointment_reminders_24h: sent %d", sent)
    return sent


@shared_task(name="agents.voice_receptionist.send_appointment_reminders_2h")
def send_appointment_reminders_2h():
    from django.utils import timezone
    from datetime import timedelta
    from agents.voice_receptionist.models import Appointment, AppointmentStatus
    from agents.voice_receptionist.notifications import notify_appointment

    now = timezone.now()
    window_start = now + timedelta(hours=1, minutes=45)
    window_end = now + timedelta(hours=2, minutes=15)

    upcoming = Appointment.objects.filter(
        scheduled_at__gte=window_start,
        scheduled_at__lte=window_end,
        status=AppointmentStatus.CONFIRMED,
    ).select_related("business")

    sent = 0
    for appt in upcoming:
        try:
            notify_appointment(appt, "reminder_2h")
            sent += 1
        except Exception as exc:
            logger.error("voice_receptionist.2h_reminder appt %s: %s", appt.id, exc)

    logger.info("voice_receptionist.send_appointment_reminders_2h: sent %d", sent)
    return sent


@shared_task(name="agents.voice_receptionist.weekly_analytics_report")
def weekly_analytics_report():
    from django.utils import timezone
    from datetime import timedelta
    from agents.voice_receptionist.models import BusinessProfile
    from agents.voice_receptionist.analytics import build_weekly_report
    from agents.voice_receptionist.engine import VoiceReceptionistEngine
    from agents.models import AgentInstance, AgentCatalog

    try:
        catalog = AgentCatalog.objects.get(slug='voice_receptionist')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = VoiceReceptionistEngine()
    end_dt = timezone.now()
    start_dt = end_dt - timedelta(days=7)
    processed = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        try:
            business_profile = BusinessProfile.objects.get(business=instance.business)
            report = build_weekly_report(business_profile, start_dt, end_dt)
            narrative = engine.weekly_performance_report(business_profile.business_name, report, instance=instance)
            logger.info("voice_receptionist.weekly_report %s: %s", business_profile.business_name, narrative[:100])
            processed += 1
        except BusinessProfile.DoesNotExist:
            pass
        except Exception as exc:
            logger.error("voice_receptionist.weekly_analytics_report instance %s: %s", instance.pk, exc)

    logger.info("voice_receptionist.weekly_analytics_report: processed %d businesses", processed)
    return processed


@shared_task(name="agents.voice_receptionist.spam_blocklist_cleanup")
def spam_blocklist_cleanup():
    from django.utils import timezone
    from datetime import timedelta
    from agents.voice_receptionist.models import SpamBlocklist

    cutoff = timezone.now() - timedelta(days=90)
    deleted, _ = SpamBlocklist.objects.filter(created_at__lt=cutoff).delete()
    logger.info("voice_receptionist.spam_blocklist_cleanup: removed %d stale entries", deleted)
    return deleted


@shared_task(name="agents.voice_receptionist.daily_call_digest")
def daily_call_digest():
    from django.utils import timezone
    from datetime import timedelta
    from agents.voice_receptionist.models import Call, BusinessProfile
    from django.db.models import Count

    yesterday = timezone.now() - timedelta(days=1)
    stats = (
        Call.objects.filter(started_at__gte=yesterday)
        .values("business__business_name", "outcome")
        .annotate(count=Count("id"))
    )
    logger.info("voice_receptionist.daily_call_digest: %s", list(stats))
    return list(stats)


@shared_task(name="agents.voice_receptionist.translate_call_transcript")
def translate_call_transcript(call_id: str):
    """
    Background task triggered after a call ends.
    Fetches the raw (native language) transcript and translates it to English using the LLM.
    """
    from agents.voice_receptionist.models import Call
    from agents.utils import agent_chat
    
    try:
        call = Call.objects.get(id=call_id)
        if not call.transcript:
            return "No transcript to translate."
        
        prompt = f"Translate the following raw phone call transcript into English. Output ONLY the English translation.\n\n{call.transcript}"
        messages = [
            {"role": "system", "content": "You are a professional translator. Translate all input text accurately into English."},
            {"role": "user", "content": prompt}
        ]
        
        english_translation = agent_chat(messages)
        
        call.english_transcript = english_translation
        call.save(update_fields=["english_transcript"])
        logger.info("voice_receptionist.translate_call_transcript: successfully translated call %s", call_id)
        return True
    except Call.DoesNotExist:
        logger.error("voice_receptionist.translate_call_transcript: Call %s not found", call_id)
        return False
    except Exception as exc:
        logger.error("voice_receptionist.translate_call_transcript call %s error: %s", call_id, exc)
        return False
