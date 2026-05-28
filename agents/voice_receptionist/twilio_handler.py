"""
voice_receptionist/twilio_handler.py
---------------------------------------
Core Twilio webhook handler — the heart of the call flow state machine.

Call Flow:
  INBOUND → spam check → STT gather → Gemini intent → TTS response → loop
  → on booking confirmed: write DB + GCal + send notifications
  → on human transfer: Twilio <Dial>
  → on spam: polite disconnect
"""

import json
import logging
from typing import Optional

import diskcache
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Session store (diskcache — replaces Redis for call state)
# ---------------------------------------------------------------------------

_session_cache: Optional[diskcache.Cache] = None


def _get_session_cache() -> diskcache.Cache:
    global _session_cache
    if _session_cache is None:
        cache_dir = Path(settings.BASE_DIR) / "cache" / "call_sessions"
        _session_cache = diskcache.Cache(str(cache_dir), size_limit=256 * 1024 * 1024)
    return _session_cache


def get_call_session(call_sid: str) -> dict:
    """Retrieve or initialize a call session from diskcache."""
    cache = _get_session_cache()
    return cache.get(f"session:{call_sid}", {
        "call_sid": call_sid,
        "turn": 0,
        "history": [],        # Gemini conversation history
        "collected": {},      # Gathered caller data so far
        "intent": None,
        "retry_count": 0,
    })


def save_call_session(call_sid: str, session: dict):
    """Persist call session to diskcache (TTL: 2 hours — max call length)."""
    cache = _get_session_cache()
    cache.set(f"session:{call_sid}", session, expire=7200)


def clear_call_session(call_sid: str):
    """Remove call session after call ends."""
    cache = _get_session_cache()
    cache.delete(f"session:{call_sid}")


# ---------------------------------------------------------------------------
# TwiML Builders
# ---------------------------------------------------------------------------

def _twiml_gather(say_text: str, action_url: str, voice_name: str = "Polly.Joanna", language: str = "en-US") -> str:
    """
    Build TwiML that speaks `say_text` then opens a <Gather> to collect caller speech.
    Uses Twilio's built-in TTS as a fallback (Google TTS audio served separately in production).
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" action="{action_url}" method="POST" speechTimeout="auto" language="{language}">
        <Say voice="{voice_name}">{say_text}</Say>
    </Gather>
    <Say voice="{voice_name}">I didn't catch that. Let me transfer you to a team member.</Say>
    <Dial>{{}}</Dial>
</Response>"""


def _twiml_say_hangup(say_text: str, voice_name: str = "Polly.Joanna") -> str:
    """TwiML to say a message and hang up (used for spam disconnect)."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice_name}">{say_text}</Say>
    <Hangup/>
</Response>"""


def _twiml_transfer(say_text: str, forward_to: str, voice_name: str = "Polly.Joanna") -> str:
    """TwiML to speak a message then dial a forwarding number."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice_name}">{say_text}</Say>
    <Dial action="/api/v1/voice/webhook/transfer-complete/" method="POST">
        <Number>{forward_to}</Number>
    </Dial>
    <Say voice="{voice_name}">Our team is unavailable right now. Please leave a message and we'll call you back.</Say>
    <Record maxLength="60" action="/api/v1/voice/webhook/voicemail/" method="POST"/>
</Response>"""


# ---------------------------------------------------------------------------
# Twilio Signature Validation
# ---------------------------------------------------------------------------

def _validate_twilio_signature(request) -> bool:
    """Validate the X-Twilio-Signature header to prevent spoofed webhooks."""
    try:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        signature = request.META.get("HTTP_X_TWILIO_SIGNATURE", "")
        url = request.build_absolute_uri()
        params = request.POST.dict()
        return validator.validate(url, params, signature)
    except Exception as e:
        logger.error("Twilio signature validation error: %s", e)
        return False


# ---------------------------------------------------------------------------
# Main Webhook Handlers
# ---------------------------------------------------------------------------

@csrf_exempt
def handle_inbound(request):
    """
    POST /api/v1/voice/webhook/inbound/
    First entry point for every inbound call from Twilio.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    # Validate Twilio signature in production
    if not settings.DEBUG and not _validate_twilio_signature(request):
        logger.warning("Invalid Twilio signature — rejecting request")
        return HttpResponse(status=403)

    call_sid     = request.POST.get("CallSid", "")
    caller_phone = request.POST.get("From", "")
    twilio_to    = request.POST.get("To", "")   # The Twilio number dialed (maps to a business)

    logger.info("Inbound call: SID=%s From=%s To=%s", call_sid, caller_phone, twilio_to)

    # Resolve the business from the Twilio number
    from .models import BusinessProfile, Call
    try:
        business = BusinessProfile.objects.get(twilio_phone_number=twilio_to, is_active=True)
    except BusinessProfile.DoesNotExist:
        logger.error("No active business found for Twilio number %s", twilio_to)
        return HttpResponse(_twiml_say_hangup("We're sorry, this number is not in service."), content_type="text/xml")

    # Pre-call spam check (blocklist + blacklist)
    from .spam_filter import run_spam_check, SpamResult
    spam = run_spam_check(caller_phone, business)
    if spam.result == SpamResult.CONFIRMED_SPAM:
        _save_call_log(call_sid, caller_phone, business, "spam", request.POST.dict())
        return HttpResponse(
            _twiml_say_hangup("Thank you for calling. Goodbye!", voice_name=business.tts_voice),
            content_type="text/xml",
        )

    # Create call log record
    Call.objects.get_or_create(
        call_sid=call_sid,
        defaults={
            "business": business,
            "caller_phone": caller_phone,
            "status": "ongoing",
            "is_after_hours": not business.is_open_now(),
            "raw_twilio_data": request.POST.dict(),
        }
    )

    # Initialize session
    session = get_call_session(call_sid)
    session["business_id"] = str(business.id)
    save_call_session(call_sid, session)

    # Build greeting
    greeting = business.greeting_template.format(
        business_name=business.business_name,
        agent_name=business.agent_name,
    )
    if not business.is_open_now():
        greeting += " We're currently closed, but I can still schedule a future appointment for you."

    action_url = f"/api/v1/voice/webhook/gather/"
    twiml = _twiml_gather(
        say_text=greeting, 
        action_url=action_url, 
        voice_name=business.tts_voice, 
        language=business.language_code
    )
    return HttpResponse(twiml, content_type="text/xml")


@csrf_exempt
def handle_gather(request):
    """
    POST /api/v1/voice/webhook/gather/
    Called after each <Gather> — processes caller speech through Gemini.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    call_sid     = request.POST.get("CallSid", "")
    caller_phone = request.POST.get("From", "")
    speech_result = request.POST.get("SpeechResult", "").strip()

    session = get_call_session(call_sid)
    session["turn"] += 1

    logger.info("Gather [turn %d] SID=%s speech='%s'", session["turn"], call_sid, speech_result[:80])

    # Silence / no speech detected
    if not speech_result:
        from .spam_filter import handle_silence_timeout
        if session["turn"] == 1:
            handle_silence_timeout(caller_phone, _get_business(session))
            return HttpResponse(_twiml_say_hangup("Thank you for calling. Goodbye!"), content_type="text/xml")
        speech_result = "[silence]"

    # Load business
    business = _get_business(session)
    if not business:
        return HttpResponse(_twiml_say_hangup("We're sorry, an error occurred. Please call back."), content_type="text/xml")

    # Post-speech spam check
    from .spam_filter import run_spam_check, SpamResult
    spam = run_spam_check(caller_phone, business, transcript=speech_result)
    if spam.result == SpamResult.CONFIRMED_SPAM:
        return HttpResponse(_twiml_say_hangup("Thank you for calling. Have a great day!", voice_name=business.tts_voice), content_type="text/xml")

    # Append caller utterance to history
    session["history"].append({"role": "user", "parts": [speech_result]})

    # Gemini intent detection
    from .ai_engine import detect_intent
    result = detect_intent(speech_result, session["history"], business)

    # Append AI response to history
    session["history"].append({"role": "model", "parts": [result.response_text]})

    # Merge collected data
    if result.collected_data:
        session["collected"].update({k: v for k, v in result.collected_data.items() if v})
    session["intent"] = result.intent.value
    save_call_session(call_sid, session)

    action_url = "/api/v1/voice/webhook/gather/"
    voice = business.tts_voice
    lang = business.language_code

    # Route based on next_action
    if result.next_action == "hangup":
        _finalize_call(call_sid, "completed")
        return HttpResponse(_twiml_say_hangup(result.response_text, voice_name=voice), content_type="text/xml")

    elif result.next_action == "transfer":
        forward_to = business.forwarding_number or settings.DEFAULT_FORWARDING_NUMBER
        _finalize_call(call_sid, "transferred")
        return HttpResponse(_twiml_transfer(result.response_text, forward_to, voice_name=voice), content_type="text/xml")

    elif result.next_action == "book":
        _confirm_booking(call_sid, session, business)
        _finalize_call(call_sid, "completed")
        closing = business.closing_template.format(
            appointment_date=session["collected"].get("preferred_datetime", "your selected time"),
            business_name=business.business_name,
        )
        return HttpResponse(_twiml_say_hangup(closing, voice_name=voice), content_type="text/xml")

    else:
        # Continue gathering
        return HttpResponse(_twiml_gather(result.response_text, action_url, voice_name=voice, language=lang), content_type="text/xml")


@csrf_exempt
def handle_voicemail(request):
    """POST /api/v1/voice/webhook/voicemail/ — Store voicemail recording URL."""
    call_sid       = request.POST.get("CallSid", "")
    recording_url  = request.POST.get("RecordingUrl", "")
    from .models import Call
    Call.objects.filter(call_sid=call_sid).update(
        recording_url=recording_url, status="voicemail"
    )
    return HttpResponse("<?xml version='1.0'?><Response><Hangup/></Response>", content_type="text/xml")


@csrf_exempt
def handle_transfer_complete(request):
    """POST /api/v1/voice/webhook/transfer-complete/ — Log transfer outcome."""
    call_sid   = request.POST.get("CallSid", "")
    dial_status = request.POST.get("DialCallStatus", "")
    from .models import Call
    Call.objects.filter(call_sid=call_sid).update(
        status="transferred" if dial_status == "completed" else "missed"
    )
    return HttpResponse("<?xml version='1.0'?><Response><Hangup/></Response>", content_type="text/xml")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_business(session: dict):
    from .models import BusinessProfile
    try:
        return BusinessProfile.objects.get(id=session.get("business_id"))
    except (BusinessProfile.DoesNotExist, Exception):
        return None


def _finalize_call(call_sid: str, status: str):
    from .models import Call
    from django.utils import timezone
    Call.objects.filter(call_sid=call_sid).update(
        status=status, ended_at=timezone.now()
    )
    # Build full transcript from session history
    session = get_call_session(call_sid)
    lines = []
    for turn in session.get("history", []):
        role  = "Caller" if turn["role"] == "user" else "AI"
        lines.append(f"[{role}]: {' '.join(turn['parts'])}")
    transcript = "\n".join(lines)
    Call.objects.filter(call_sid=call_sid).update(transcript=transcript)
    clear_call_session(call_sid)
    
    # Trigger background translation to English
    try:
        call_obj = Call.objects.filter(call_sid=call_sid).first()
        if call_obj and transcript.strip():
            from .tasks import translate_call_transcript
            translate_call_transcript.delay(str(call_obj.id))
    except Exception as e:
        logger.error("Failed to trigger translation task for call %s: %s", call_sid, e)


def _confirm_booking(call_sid: str, session: dict, business):
    """Create Appointment record + sync to Google Calendar + send notifications."""
    from .models import Call, Appointment
    from .calendar_sync import create_appointment_event
    from .notifications import notify_appointment
    from django.utils.dateparse import parse_datetime

    data = session.get("collected", {})
    call = Call.objects.filter(call_sid=call_sid).first()

    scheduled_at = None
    raw_dt = data.get("preferred_datetime", "")
    if raw_dt:
        try:
            scheduled_at = parse_datetime(raw_dt)
        except Exception:
            pass

    if not scheduled_at:
        from django.utils import timezone
        scheduled_at = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)

    appointment = Appointment.objects.create(
        business=business,
        call=call,
        caller_name=data.get("caller_name", "Unknown Caller"),
        caller_phone=data.get("caller_phone", call.caller_phone if call else ""),
        service_type=data.get("service_type", "General Appointment"),
        scheduled_at=scheduled_at,
        address=data.get("address", ""),
        insurance_type=data.get("insurance_type", ""),
        preferred_staff=data.get("preferred_staff", ""),
        notes=data.get("notes", ""),
        status="confirmed",
    )

    # Google Calendar sync
    event_id = create_appointment_event(business, appointment)
    if event_id:
        appointment.gcal_event_id = event_id
        appointment.calendar_synced = True
        appointment.save(update_fields=["gcal_event_id", "calendar_synced"])

    # Send confirmation notifications
    notify_appointment(appointment, "booking_confirmed")
    logger.info("Appointment created: %s for %s", appointment.id, appointment.caller_name)


def _save_call_log(call_sid: str, caller_phone: str, business, status: str, raw_data: dict):
    from .models import Call
    Call.objects.get_or_create(
        call_sid=call_sid,
        defaults={
            "business": business,
            "caller_phone": caller_phone,
            "status": status,
            "raw_twilio_data": raw_data,
        }
    )
