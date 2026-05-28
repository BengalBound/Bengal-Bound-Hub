"""
voice_receptionist/notifications.py
--------------------------------------
SMS (Twilio) and Email (Gmail SMTP via Django send_mail) notification service.
Templates are stored in NotificationTemplate model with variable substitution.
"""

import logging
from typing import Optional

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

# Default templates (used if no custom template exists in DB)
DEFAULT_TEMPLATES = {
    "booking_confirmed": {
        "sms": "Hi {client_name}, your {service_type} appointment at {business_name} is confirmed for {appointment_time}. We look forward to seeing you!",
        "email_subject": "Appointment Confirmed — {business_name}",
        "email": (
            "Hi {client_name},\n\n"
            "Your {service_type} appointment with {business_name} has been confirmed.\n\n"
            "Date & Time: {appointment_time}\n"
            "Questions? Call us at {business_phone}.\n\n"
            "See you soon!\n— {agent_name} @ {business_name}"
        ),
    },
    "booking_cancelled": {
        "sms": "Hi {client_name}, your {service_type} appointment at {business_name} on {appointment_time} has been cancelled. Call us to rebook.",
        "email_subject": "Appointment Cancelled — {business_name}",
        "email": (
            "Hi {client_name},\n\n"
            "Your {service_type} appointment on {appointment_time} has been cancelled.\n"
            "Please call or visit our website to schedule a new time.\n\n"
            "— {agent_name} @ {business_name}"
        ),
    },
    "booking_rescheduled": {
        "sms": "Hi {client_name}, your appointment at {business_name} has been rescheduled to {appointment_time}.",
        "email_subject": "Appointment Rescheduled — {business_name}",
        "email": (
            "Hi {client_name},\n\n"
            "Your appointment has been rescheduled.\n\n"
            "New Date & Time: {appointment_time}\n"
            "Service: {service_type}\n\n"
            "— {agent_name} @ {business_name}"
        ),
    },
    "reminder_24h": {
        "sms": "Reminder: {client_name}, you have a {service_type} appointment at {business_name} tomorrow at {appointment_time}. Reply STOP to opt out.",
        "email_subject": "Appointment Reminder — {business_name}",
        "email": (
            "Hi {client_name},\n\n"
            "This is a reminder that your {service_type} appointment is tomorrow at {appointment_time}.\n\n"
            "— {agent_name} @ {business_name}"
        ),
    },
    "reminder_2h": {
        "sms": "Heads up {client_name}! Your {service_type} at {business_name} is in 2 hours ({appointment_time}). See you soon!",
        "email_subject": None,  # 2h reminder: SMS only
        "email": None,
    },
    "missed_call": {
        "sms": None,
        "email_subject": "Missed Call Notification — {business_name}",
        "email": (
            "Hello,\n\n"
            "You missed a call from {caller_phone} at {appointment_time}.\n"
            "The caller left the following message: {notes}\n\n"
            "— Bengal Bound AI Receptionist"
        ),
    },
}


def _render_template(template_str: Optional[str], context: dict) -> Optional[str]:
    """Replace {variable} placeholders in a template string."""
    if not template_str:
        return None
    try:
        return template_str.format(**context)
    except KeyError as e:
        logger.warning("Missing template variable %s — using raw template", e)
        return template_str


def _get_template(business, trigger_type: str) -> dict:
    """Fetch custom template from DB; fall back to DEFAULT_TEMPLATES."""
    from .models import NotificationTemplate
    try:
        tmpl = NotificationTemplate.objects.get(business=business, trigger_type=trigger_type, is_active=True)
        return {
            "sms": tmpl.sms_template or None,
            "email_subject": tmpl.email_subject or None,
            "email": tmpl.email_template or None,
        }
    except NotificationTemplate.DoesNotExist:
        return DEFAULT_TEMPLATES.get(trigger_type, {})


def _build_context(business, appointment=None, caller_phone: str = "", extra: dict = None) -> dict:
    ctx = {
        "business_name":    business.business_name,
        "agent_name":       business.agent_name,
        "business_phone":   business.phone,
        "caller_phone":     caller_phone,
        "client_name":      "",
        "service_type":     "",
        "appointment_time": "",
        "appointment_date": "",
        "notes":            "",
    }
    if appointment:
        ctx["client_name"]      = appointment.caller_name
        ctx["service_type"]     = appointment.service_type
        ctx["caller_phone"]     = appointment.caller_phone
        ctx["notes"]            = appointment.notes
        ctx["appointment_time"] = appointment.scheduled_at.strftime("%A, %B %d at %I:%M %p")
        ctx["appointment_date"] = appointment.scheduled_at.strftime("%A, %B %d")
    if extra:
        ctx.update(extra)
    return ctx


# ---------------------------------------------------------------------------
# Public Send Functions
# ---------------------------------------------------------------------------

def send_sms(to_number: str, trigger_type: str, business, appointment=None, extra: dict = None):
    """Send an SMS notification via Twilio."""
    tmpl = _get_template(business, trigger_type)
    context = _build_context(business, appointment, to_number, extra)
    body = _render_template(tmpl.get("sms"), context)
    if not body:
        logger.debug("No SMS template for trigger %s — skipping", trigger_type)
        return

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_number,
        )
        logger.info("SMS sent to %s (SID: %s)", to_number, message.sid)
    except Exception as e:
        logger.error("SMS send failed to %s: %s", to_number, e)


def send_email(to_email: str, trigger_type: str, business, appointment=None, extra: dict = None):
    """Send an email notification via Django's configured EMAIL_BACKEND (Gmail SMTP)."""
    if not to_email:
        return
    tmpl = _get_template(business, trigger_type)
    context = _build_context(business, appointment, extra=extra)
    subject = _render_template(tmpl.get("email_subject"), context)
    body    = _render_template(tmpl.get("email"), context)
    if not subject or not body:
        logger.debug("No email template for trigger %s — skipping", trigger_type)
        return

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[to_email],
            fail_silently=False,
        )
        logger.info("Email sent to %s [trigger: %s]", to_email, trigger_type)
    except Exception as e:
        logger.error("Email send failed to %s: %s", to_email, e)


def notify_appointment(appointment, trigger_type: str):
    """
    Convenience: fire both SMS + email for client and business owner
    for a given appointment event (confirmed / cancelled / rescheduled).
    """
    business = appointment.business

    # Notify client
    send_sms(appointment.caller_phone, trigger_type, business, appointment)
    if appointment.caller_email:
        send_email(appointment.caller_email, trigger_type, business, appointment)

    # Notify business owner (email only — SMS optional)
    owner_email = getattr(settings, "BUSINESS_OWNER_EMAIL", None)
    if owner_email:
        send_email(owner_email, trigger_type, business, appointment)
