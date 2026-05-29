"""
voice_receptionist/analytics.py
---------------------------------
Analytics query functions for the dashboard and weekly report.
All queries use Django ORM — no raw SQL required for Phase 1.
"""

import logging
from datetime import datetime
from django.db.models import Count, Avg

logger = logging.getLogger(__name__)


def build_analytics(business, start_dt: datetime, end_dt: datetime) -> dict:
    """
    Build full analytics summary for a business in a given date range.

    Returns a dict matching AnalyticsSummarySerializer fields.
    """
    from .models import Call, Appointment, SpamLog, CallStatus, AppointmentStatus

    calls = Call.objects.filter(business=business, started_at__range=(start_dt, end_dt))
    appointments = Appointment.objects.filter(business=business, created_at__range=(start_dt, end_dt))

    total_calls       = calls.count()
    completed_calls   = calls.filter(status=CallStatus.COMPLETED).count()
    spam_blocked      = calls.filter(status=CallStatus.SPAM).count() + \
                        SpamLog.objects.filter(business=business, detected_at__range=(start_dt, end_dt)).count()
    transferred_calls = calls.filter(status=CallStatus.TRANSFERRED).count()
    appointments_booked = appointments.filter(status__in=[
        AppointmentStatus.CONFIRMED, AppointmentStatus.RESCHEDULED, AppointmentStatus.COMPLETED
    ]).count()
    cancelled = appointments.filter(status=AppointmentStatus.CANCELLED).count()

    booking_rate = (appointments_booked / total_calls * 100) if total_calls else 0.0
    spam_rate    = (spam_blocked / total_calls * 100)         if total_calls else 0.0
    cancel_rate  = (cancelled / appointments_booked * 100)    if appointments_booked else 0.0

    avg_duration_qs = calls.filter(duration_seconds__isnull=False).aggregate(Avg("duration_seconds"))
    avg_duration    = avg_duration_qs.get("duration_seconds__avg")

    # Peak hour: find the hour (0-23) with the most calls
    from django.db.models.functions import ExtractHour
    hour_qs = (
        calls
        .annotate(hour=ExtractHour("started_at"))
        .values("hour")
        .annotate(c=Count("id"))
        .order_by("-c")
        .first()
    )
    peak_hour = hour_qs["hour"] if hour_qs else None

    # Top services
    top_services = (
        appointments
        .values("service_type")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )
    top_services_list = [{"service": s["service_type"], "count": s["count"]} for s in top_services]

    return {
        "total_calls":           total_calls,
        "completed_calls":       completed_calls,
        "spam_blocked":          spam_blocked,
        "transferred_calls":     transferred_calls,
        "appointments_booked":   appointments_booked,
        "booking_rate_pct":      round(booking_rate, 1),
        "spam_rate_pct":         round(spam_rate, 1),
        "avg_duration_seconds":  round(avg_duration, 1) if avg_duration else None,
        "peak_hour":             peak_hour,
        "top_services":          top_services_list,
        "cancellation_rate_pct": round(cancel_rate, 1),
    }


def build_weekly_report(business, start_dt: datetime, end_dt: datetime) -> dict:
    """Convenience wrapper for the weekly email report job."""
    return build_analytics(business, start_dt, end_dt)
