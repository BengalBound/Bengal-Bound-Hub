"""
voice_receptionist/scheduler.py
---------------------------------
APScheduler background jobs for:
 - 24-hour appointment reminders
 - 2-hour appointment reminders
 - Weekly analytics email report

Uses django-apscheduler to persist job state in the Django database.
No Redis or Celery required — runs in-process.
"""

import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

_scheduler = None


def start_scheduler():
    """Initialize and start the APScheduler background scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        from django_apscheduler.jobstores import DjangoJobStore

        _scheduler = BackgroundScheduler(timezone="UTC")
        _scheduler.add_jobstore(DjangoJobStore(), "default")

        # 24-hour reminders — check every hour
        _scheduler.add_job(
            func=send_24h_reminders,
            trigger=IntervalTrigger(hours=1),
            id="send_24h_reminders",
            name="Send 24-Hour Appointment Reminders",
            replace_existing=True,
            misfire_grace_time=300,
        )

        # 2-hour reminders — check every 15 minutes
        _scheduler.add_job(
            func=send_2h_reminders,
            trigger=IntervalTrigger(minutes=15),
            id="send_2h_reminders",
            name="Send 2-Hour Appointment Reminders",
            replace_existing=True,
            misfire_grace_time=120,
        )

        # Weekly analytics report — every Monday at 8am UTC
        _scheduler.add_job(
            func=send_weekly_reports,
            trigger="cron",
            day_of_week="mon",
            hour=8,
            minute=0,
            id="send_weekly_reports",
            name="Send Weekly Analytics Reports",
            replace_existing=True,
        )

        _scheduler.start()
        logger.info("APScheduler started with %d jobs", len(_scheduler.get_jobs()))

    except Exception as e:
        logger.error("Failed to start APScheduler: %s", e)


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")


# ---------------------------------------------------------------------------
# Job Functions
# ---------------------------------------------------------------------------

def send_24h_reminders():
    """Find appointments in ~24 hours and send SMS reminders (if not already sent)."""
    from django.utils import timezone
    from .models import Appointment, AppointmentStatus
    from .notifications import notify_appointment

    now = timezone.now()
    window_start = now + timedelta(hours=23, minutes=30)
    window_end   = now + timedelta(hours=24, minutes=30)

    upcoming = Appointment.objects.filter(
        scheduled_at__gte=window_start,
        scheduled_at__lte=window_end,
        status=AppointmentStatus.CONFIRMED,
    ).select_related("business")

    count = upcoming.count()
    if count == 0:
        return

    logger.info("Sending 24h reminders for %d appointments", count)
    for appt in upcoming:
        try:
            notify_appointment(appt, "reminder_24h")
        except Exception as e:
            logger.error("24h reminder failed for appointment %s: %s", appt.id, e)


def send_2h_reminders():
    """Find appointments in ~2 hours and send SMS reminders."""
    from django.utils import timezone
    from .models import Appointment, AppointmentStatus
    from .notifications import notify_appointment

    now = timezone.now()
    window_start = now + timedelta(hours=1, minutes=45)
    window_end   = now + timedelta(hours=2, minutes=15)

    upcoming = Appointment.objects.filter(
        scheduled_at__gte=window_start,
        scheduled_at__lte=window_end,
        status=AppointmentStatus.CONFIRMED,
    ).select_related("business")

    count = upcoming.count()
    if count == 0:
        return

    logger.info("Sending 2h reminders for %d appointments", count)
    for appt in upcoming:
        try:
            notify_appointment(appt, "reminder_2h")
        except Exception as e:
            logger.error("2h reminder failed for appointment %s: %s", appt.id, e)


def send_weekly_reports():
    """Email a weekly analytics summary to each active business owner."""
    from .models import BusinessProfile
    from .analytics import build_weekly_report
    from .notifications import send_email
    from django.utils import timezone
    from django.conf import settings

    end_dt   = timezone.now()
    start_dt = end_dt - timedelta(days=7)

    businesses = BusinessProfile.objects.filter(is_active=True)
    logger.info("Sending weekly reports to %d businesses", businesses.count())

    for business in businesses:
        try:
            report = build_weekly_report(business, start_dt, end_dt)
            owner_email = getattr(settings, "BUSINESS_OWNER_EMAIL", None)
            if owner_email:
                send_email(
                    to_email=owner_email,
                    trigger_type="weekly_report",
                    business=business,
                    extra={
                        "total_calls":   report["total_calls"],
                        "bookings":      report["appointments_booked"],
                        "spam_blocked":  report["spam_blocked"],
                        "booking_rate":  f"{report['booking_rate_pct']:.1f}%",
                    },
                )
        except Exception as e:
            logger.error("Weekly report failed for %s: %s", business.business_name, e)
