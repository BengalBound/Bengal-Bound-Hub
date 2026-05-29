"""
voice_receptionist/calendar_sync.py
--------------------------------------
Google Calendar OAuth 2.0 integration.
Phase 1: Google Calendar only.
Phase 2: Outlook, iCal, Acuity, Calendly.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token encryption/decryption (Fernet — symmetric key from settings)
# ---------------------------------------------------------------------------

def _encrypt_token(token_dict: dict) -> str:
    from cryptography.fernet import Fernet
    f = Fernet(settings.CALENDAR_ENCRYPTION_KEY.encode())
    return f.encrypt(json.dumps(token_dict).encode()).decode()


def _decrypt_token(encrypted_str: str) -> dict:
    from cryptography.fernet import Fernet
    f = Fernet(settings.CALENDAR_ENCRYPTION_KEY.encode())
    return json.loads(f.decrypt(encrypted_str.encode()).decode())


# ---------------------------------------------------------------------------
# OAuth Token Management
# ---------------------------------------------------------------------------

def get_google_calendar_service(business_profile):
    """
    Build and return an authorized Google Calendar API service object.
    Refreshes the access token automatically if expired.
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    if not business_profile.calendar_token:
        raise ValueError("No Google Calendar token stored for this business. Please connect your calendar first.")

    token_data = _decrypt_token(business_profile.calendar_token)
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes", ["https://www.googleapis.com/auth/calendar"]),
    )

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Persist refreshed token
        token_data["token"] = creds.token
        business_profile.calendar_token = _encrypt_token(token_data)
        business_profile.save(update_fields=["calendar_token"])
        logger.info("Refreshed Google Calendar token for %s", business_profile.business_name)

    service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    return service


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------

def get_available_slots(
    business_profile,
    start_dt: datetime,
    end_dt: datetime,
    slot_duration_minutes: int = 60,
) -> list[datetime]:
    """
    Return a list of available datetime slots in [start_dt, end_dt].
    Checks busy/free via Google Calendar freebusy query.
    Applies business hours and buffer time.

    Returns:
        List of naive or timezone-aware datetime objects (tz-aware preferred).
    """
    try:
        service = get_google_calendar_service(business_profile)
        calendar_id = business_profile.calendar_id or "primary"

        body = {
            "timeMin": start_dt.isoformat(),
            "timeMax": end_dt.isoformat(),
            "items": [{"id": calendar_id}],
        }
        result = service.freebusy().query(body=body).execute()
        busy_periods = result["calendars"].get(calendar_id, {}).get("busy", [])

        # Parse busy periods
        busy_intervals = []
        for period in busy_periods:
            b_start = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
            b_end   = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))
            busy_intervals.append((b_start, b_end))

        # Generate candidate slots
        buffer = timedelta(minutes=business_profile.buffer_minutes)
        slot_len = timedelta(minutes=slot_duration_minutes)
        available = []
        current = start_dt
        while current + slot_len <= end_dt:
            slot_end = current + slot_len
            # Check if slot overlaps any busy period
            is_busy = any(
                not (slot_end + buffer <= b[0] or current >= b[1] + buffer)
                for b in busy_intervals
            )
            if not is_busy and _within_business_hours(business_profile, current, slot_end):
                available.append(current)
            current += timedelta(minutes=30)  # 30-minute interval between candidate starts

        return available[:6]  # Return max 6 options per query

    except Exception as e:
        logger.error("Calendar freebusy error for %s: %s", business_profile.business_name, e)
        return []


def _within_business_hours(business_profile, slot_start: datetime, slot_end: datetime) -> bool:
    """Return True if slot_start..slot_end falls within configured business hours."""
    hours = business_profile.business_hours
    if not hours:
        return True  # If no hours configured, treat as always open
    day_name = slot_start.strftime("%A").lower()
    day_hours = hours.get(day_name)
    if not day_hours:
        return False  # Closed this day
    from datetime import time as dt_time
    open_h, open_m   = map(int, day_hours["open"].split(":"))
    close_h, close_m = map(int, day_hours["close"].split(":"))
    open_time  = dt_time(open_h, open_m)
    close_time = dt_time(close_h, close_m)
    return open_time <= slot_start.time() and slot_end.time() <= close_time


# ---------------------------------------------------------------------------
# CRUD Calendar Events
# ---------------------------------------------------------------------------

def create_appointment_event(business_profile, appointment) -> Optional[str]:
    """
    Create a Google Calendar event for a confirmed appointment.
    Returns the event ID on success, None on failure.
    """
    try:
        service = get_google_calendar_service(business_profile)
        calendar_id = business_profile.calendar_id or "primary"

        end_dt = appointment.scheduled_at + timedelta(hours=1)
        event = {
            "summary": f"{appointment.service_type} — {appointment.caller_name}",
            "description": (
                f"Caller: {appointment.caller_name}\n"
                f"Phone: {appointment.caller_phone}\n"
                f"Service: {appointment.service_type}\n"
                f"Notes: {appointment.notes}\n"
                f"Booked via Bengal Bound AI Receptionist"
            ),
            "start": {"dateTime": appointment.scheduled_at.isoformat(), "timeZone": "UTC"},
            "end":   {"dateTime": end_dt.isoformat(), "timeZone": "UTC"},
            "reminders": {"useDefault": True},
        }
        created = service.events().insert(calendarId=calendar_id, body=event).execute()
        event_id = created.get("id")
        logger.info("Created GCal event %s for %s", event_id, appointment.caller_name)
        return event_id

    except Exception as e:
        logger.error("Failed to create GCal event: %s", e)
        return None


def update_appointment_event(business_profile, appointment) -> bool:
    """Update an existing Google Calendar event. Returns True on success."""
    if not appointment.gcal_event_id:
        return False
    try:
        service = get_google_calendar_service(business_profile)
        calendar_id = business_profile.calendar_id or "primary"

        end_dt = appointment.scheduled_at + timedelta(hours=1)
        event = {
            "summary": f"{appointment.service_type} — {appointment.caller_name}",
            "start": {"dateTime": appointment.scheduled_at.isoformat(), "timeZone": "UTC"},
            "end":   {"dateTime": end_dt.isoformat(), "timeZone": "UTC"},
        }
        service.events().update(
            calendarId=calendar_id, eventId=appointment.gcal_event_id, body=event
        ).execute()
        logger.info("Updated GCal event %s", appointment.gcal_event_id)
        return True

    except Exception as e:
        logger.error("Failed to update GCal event %s: %s", appointment.gcal_event_id, e)
        return False


def delete_appointment_event(business_profile, gcal_event_id: str) -> bool:
    """Delete a Google Calendar event. Returns True on success."""
    try:
        service = get_google_calendar_service(business_profile)
        calendar_id = business_profile.calendar_id or "primary"
        service.events().delete(calendarId=calendar_id, eventId=gcal_event_id).execute()
        logger.info("Deleted GCal event %s", gcal_event_id)
        return True
    except Exception as e:
        logger.error("Failed to delete GCal event %s: %s", gcal_event_id, e)
        return False
