"""
voice_receptionist/models.py
----------------------------
All Django ORM models for the Bengal Bound Voice Receptionist module.
Uses existing PostgreSQL (production) / SQLite (test via Django TEST config).
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

class BusinessType(models.TextChoices):
    PLUMBER  = "plumber",  "Plumber / HVAC"
    DENTIST  = "dentist",  "Dentist / Clinic"
    SALON    = "salon",    "Salon / Spa"
    GENERAL  = "general",  "General Service"


class CalendarType(models.TextChoices):
    GOOGLE   = "google",   "Google Calendar"
    OUTLOOK  = "outlook",  "Microsoft Outlook"
    APPLE    = "apple",    "Apple iCloud"
    ACUITY   = "acuity",   "Acuity Scheduling"
    CALENDLY = "calendly", "Calendly"
    ICAL     = "ical",     "Generic iCal Feed"
    NONE     = "none",     "None / Manual"


class CallStatus(models.TextChoices):
    ONGOING     = "ongoing",      "Ongoing"
    COMPLETED   = "completed",    "Completed"
    SPAM        = "spam",         "Spam / Blocked"
    TRANSFERRED = "transferred",  "Transferred to Human"
    MISSED      = "missed",       "Missed / After-Hours"
    VOICEMAIL   = "voicemail",    "Voicemail Left"


class AppointmentStatus(models.TextChoices):
    CONFIRMED    = "confirmed",    "Confirmed"
    CANCELLED    = "cancelled",    "Cancelled"
    RESCHEDULED  = "rescheduled",  "Rescheduled"
    PENDING      = "pending",      "Pending Approval"
    COMPLETED    = "completed",    "Completed"


class SpamAction(models.TextChoices):
    DISCONNECTED  = "disconnected",   "Disconnected"
    FLAGGED       = "flagged",        "Flagged for Review"
    ALLOWED       = "allowed",        "Allowed Through"


class UserRole(models.TextChoices):
    ADMIN   = "admin",   "Admin"
    MANAGER = "manager", "Manager"
    STAFF   = "staff",   "Staff (Read-Only)"


class NotificationTrigger(models.TextChoices):
    BOOKING_CONFIRMED  = "booking_confirmed",   "New Booking Confirmed"
    BOOKING_CANCELLED  = "booking_cancelled",   "Booking Cancelled"
    BOOKING_RESCHEDULED = "booking_rescheduled","Booking Rescheduled"
    REMINDER_24H       = "reminder_24h",        "24-Hour Reminder"
    REMINDER_2H        = "reminder_2h",         "2-Hour Reminder"
    MISSED_CALL        = "missed_call",          "Missed Call"
    WEEKLY_REPORT      = "weekly_report",        "Weekly Analytics Report"


# ---------------------------------------------------------------------------
# BusinessProfile
# ---------------------------------------------------------------------------

class BusinessProfile(models.Model):
    """
    One profile per business tenant.
    Linked to Firebase UID (stored on UserProfile).
    """
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firebase_uid        = models.CharField(max_length=128, unique=True, db_index=True)
    business_name       = models.CharField(max_length=200)
    business_type       = models.CharField(max_length=20, choices=BusinessType.choices, default=BusinessType.GENERAL)
    phone               = models.CharField(max_length=30, help_text="Business's own phone number")
    forwarding_number   = models.CharField(max_length=30, blank=True, help_text="Number to transfer calls to when escalating")
    twilio_phone_number = models.CharField(max_length=30, blank=True, help_text="Assigned Twilio number for this business")
    agent_name          = models.CharField(max_length=100, default="Aria", help_text="AI agent's display name")
    tts_voice           = models.CharField(max_length=60, default="en-US-Neural2-F", help_text="Google Cloud TTS voice ID")
    greeting_template   = models.TextField(
        default="Thank you for calling {business_name}. My name is {agent_name}. How can I help you today?"
    )
    closing_template    = models.TextField(
        default="You're all set! We'll see you on {appointment_date}. Have a great day!"
    )
    # Business Hours stored as JSON: {"monday": {"open": "09:00", "close": "17:00"}, ...}
    business_hours      = models.JSONField(default=dict, blank=True)
    min_lead_time_hours = models.PositiveIntegerField(default=2, help_text="Minimum hours before a booking is allowed")
    buffer_minutes      = models.PositiveIntegerField(default=15, help_text="Buffer time between appointments")
    # Calendar
    calendar_type       = models.CharField(max_length=20, choices=CalendarType.choices, default=CalendarType.NONE)
    calendar_token      = models.TextField(blank=True, help_text="Encrypted OAuth2 token JSON")
    calendar_id         = models.CharField(max_length=255, blank=True, help_text="Google Calendar ID or equivalent")
    # Staff list stored as JSON list of names
    staff_list          = models.JSONField(default=list, blank=True)
    # Services offered (list of strings)
    services_offered    = models.JSONField(default=list, blank=True)
    is_active           = models.BooleanField(default=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Business Profile"
        verbose_name_plural = "Business Profiles"
        ordering = ["business_name"]

    def __str__(self):
        return f"{self.business_name} ({self.get_business_type_display()})"

    def is_open_now(self):
        """Return True if the business is currently within its operating hours."""
        now = timezone.localtime()
        day_name = now.strftime("%A").lower()  # e.g. 'monday'
        hours = self.business_hours.get(day_name)
        if not hours:
            return False
        from datetime import time as dt_time
        open_h, open_m  = map(int, hours["open"].split(":"))
        close_h, close_m = map(int, hours["close"].split(":"))
        open_time  = dt_time(open_h,  open_m)
        close_time = dt_time(close_h, close_m)
        return open_time <= now.time() < close_time


# ---------------------------------------------------------------------------
# Call
# ---------------------------------------------------------------------------

class Call(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business        = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="calls")
    call_sid        = models.CharField(max_length=64, unique=True, db_index=True, help_text="Twilio Call SID")
    caller_phone    = models.CharField(max_length=30)
    caller_name     = models.CharField(max_length=200, blank=True)
    status          = models.CharField(max_length=20, choices=CallStatus.choices, default=CallStatus.ONGOING)
    transcript      = models.TextField(blank=True)
    recording_url   = models.URLField(blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    started_at      = models.DateTimeField(default=timezone.now)
    ended_at        = models.DateTimeField(null=True, blank=True)
    # Metadata
    is_after_hours  = models.BooleanField(default=False)
    escalated_to_human = models.BooleanField(default=False)
    raw_twilio_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Call"
        verbose_name_plural = "Call Log"
        ordering = ["-started_at"]

    def __str__(self):
        return f"Call from {self.caller_phone} [{self.status}] @ {self.started_at:%Y-%m-%d %H:%M}"


# ---------------------------------------------------------------------------
# Appointment
# ---------------------------------------------------------------------------

class Appointment(models.Model):
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business          = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="appointments")
    call              = models.OneToOneField(Call, null=True, blank=True, on_delete=models.SET_NULL, related_name="appointment")
    caller_name       = models.CharField(max_length=200)
    caller_phone      = models.CharField(max_length=30)
    caller_email      = models.EmailField(blank=True)
    service_type      = models.CharField(max_length=200)
    scheduled_at      = models.DateTimeField()
    status            = models.CharField(max_length=20, choices=AppointmentStatus.choices, default=AppointmentStatus.CONFIRMED)
    # Business-type-specific fields
    address           = models.TextField(blank=True, help_text="Plumber: on-site service address")
    insurance_type    = models.CharField(max_length=100, blank=True, help_text="Dental: insurance carrier")
    preferred_staff   = models.CharField(max_length=200, blank=True, help_text="Salon: preferred stylist/staff")
    notes             = models.TextField(blank=True)
    # Calendar sync
    gcal_event_id     = models.CharField(max_length=255, blank=True, help_text="Google Calendar event ID")
    calendar_synced   = models.BooleanField(default=False)
    # Recurring
    is_recurring      = models.BooleanField(default=False)
    recur_interval_weeks = models.PositiveIntegerField(null=True, blank=True)
    parent_appointment   = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="recurrences"
    )
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"
        ordering = ["scheduled_at"]

    def __str__(self):
        return f"{self.caller_name} — {self.service_type} @ {self.scheduled_at:%Y-%m-%d %H:%M} [{self.status}]"


# ---------------------------------------------------------------------------
# SpamLog
# ---------------------------------------------------------------------------

class SpamLog(models.Model):
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business         = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="spam_logs")
    caller_phone     = models.CharField(max_length=30, db_index=True)
    detected_at      = models.DateTimeField(default=timezone.now)
    detection_reason = models.CharField(max_length=500)
    action_taken     = models.CharField(max_length=20, choices=SpamAction.choices, default=SpamAction.FLAGGED)
    transcript_snippet = models.TextField(blank=True)
    # Admin-controlled overrides
    is_whitelisted   = models.BooleanField(default=False)
    is_blacklisted   = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Spam Log Entry"
        verbose_name_plural = "Spam Log"
        ordering = ["-detected_at"]

    def __str__(self):
        return f"Spam: {self.caller_phone} [{self.action_taken}] @ {self.detected_at:%Y-%m-%d %H:%M}"


class SpamBlocklist(models.Model):
    """Static community blocklist — managed via update_spam_blocklist management command."""
    phone_number = models.CharField(max_length=30, unique=True, db_index=True)
    source       = models.CharField(max_length=100, default="community")
    added_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Spam Blocklist Entry"
        verbose_name_plural = "Spam Blocklist"

    def __str__(self):
        return self.phone_number


# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------

class UserProfile(models.Model):
    """
    Extends Django's User model with Firebase UID and role.
    Created/updated on each authenticated API request.
    """
    user         = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="voice_profile")
    firebase_uid = models.CharField(max_length=128, unique=True, db_index=True)
    role         = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.STAFF)
    business     = models.ForeignKey(BusinessProfile, null=True, blank=True, on_delete=models.SET_NULL)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username} [{self.role}]"


# ---------------------------------------------------------------------------
# NotificationTemplate
# ---------------------------------------------------------------------------

class NotificationTemplate(models.Model):
    """
    Customizable SMS + email templates per business per trigger type.
    Variables: {client_name}, {appointment_time}, {service_type}, {business_name}, {agent_name}
    """
    business      = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="notification_templates")
    trigger_type  = models.CharField(max_length=40, choices=NotificationTrigger.choices)
    sms_template  = models.TextField(blank=True)
    email_subject = models.CharField(max_length=255, blank=True)
    email_template = models.TextField(blank=True)
    is_active     = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"
        unique_together = [("business", "trigger_type")]

    def __str__(self):
        return f"{self.business.business_name} — {self.get_trigger_type_display()}"
