# Module Requirements: Aria — AI Voice Receptionist
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `aria` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) + Google Cloud STT/TTS | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Twilio Voice, Google Cloud Speech-to-Text, Google Cloud Text-to-Speech, Google Calendar

---

## Section 1: Overview

**AI Employee Name:** Aria | **Department:** Front Desk / Communications
**Target Clients:** Law firms, clinics, real estate agencies, consulting firms, e-commerce brands — any business with inbound phone calls needing professional handling 24/7.
**Core Function:** Answers every inbound call in the client's brand voice, qualifies callers, books appointments, filters spam calls, syncs the calendar, and sends SMS/email confirmations — never on sick leave, never misses a call.
**Value Prop:** *"Your phone gets answered every time. Every caller leaves happy. Zero receptionist overhead."*

| | Human Receptionist | Aria AI |
|---|---|---|
| Monthly Cost | ৳15,000–৳25,000 | ৳2,000 |
| Availability | Business hours | 24/7/365 |
| Simultaneous Calls | 1 | Unlimited |
| Consistency | Variable | 100% on-brand |

---

## Section 2: Core Capabilities

1. **Inbound Call Handling** — Twilio routes all calls to Aria; she greets in the client's brand voice (custom name, tone)
2. **Caller Intent Detection** — STT converts speech to text; Gemini classifies: appointment, inquiry, support, sales, spam
3. **Appointment Booking** — Checks Google Calendar availability; books slot; confirms via voice + SMS
4. **FAQ Answering** — Answers common questions from the knowledge base (hours, location, pricing, services)
5. **Intelligent Routing** — If caller needs a specific person, routes to their extension or mobile; takes a message if unavailable
6. **Spam/Robocall Filter** — Detects automated spam callers and hangs up with a polite message
7. **Call Transcription & Summary** — Every call transcribed; Gemini generates a 3-line summary logged to dashboard
8. **After-Call SMS** — Sends caller a confirmation SMS with booking details, address, or follow-up information

---

## Section 3: Django Models

```python
class AriaConfig(models.Model):
    business            = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='aria_ariaconfigs')
    receptionist_name   = models.CharField(max_length=100, default='Aria')
    business_name       = models.CharField(max_length=300)
    greeting_script     = models.TextField()
    voice_gender        = models.CharField(max_length=10, default='female')  # Google TTS voice
    language_code       = models.CharField(max_length=10, default='en-US')
    twilio_number       = models.CharField(max_length=30)
    calendar_id         = models.CharField(max_length=300, blank=True)
    after_hours_message = models.TextField(blank=True)
    spam_sensitivity    = models.IntegerField(default=70)    # 0–100 threshold

class KnowledgeBase(models.Model):
    business    = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='aria_knowledgebases')
    question    = models.TextField()
    answer      = models.TextField()
    category    = models.CharField(max_length=100, blank=True)
    is_active   = models.BooleanField(default=True)

class CallLog(models.Model):
    STATUS = [('completed','Completed'),('missed','Missed'),('spam','Spam'),
              ('transferred','Transferred'),('voicemail','Voicemail')]
    INTENT = [('appointment','Appointment'),('inquiry','Inquiry'),('support','Support'),
              ('sales','Sales'),('spam','Spam'),('other','Other')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='aria_calllogs')
    twilio_call_sid = models.CharField(max_length=200, unique=True)
    caller_number   = models.CharField(max_length=30)
    caller_name     = models.CharField(max_length=300, blank=True)
    duration        = models.IntegerField(null=True)         # Seconds
    intent          = models.CharField(max_length=20, choices=INTENT)
    status          = models.CharField(max_length=20, choices=STATUS)
    transcript      = models.TextField(blank=True)
    ai_summary      = models.TextField(blank=True)           # Gemini 3-line summary
    appointment_booked = models.BooleanField(default=False)
    appointment_time   = models.DateTimeField(null=True)
    sms_sent        = models.BooleanField(default=False)
    is_spam         = models.BooleanField(default=False)
    received_at     = models.DateTimeField()
    ended_at        = models.DateTimeField(null=True)

class Voicemail(models.Model):
    call_log        = models.ForeignKey(CallLog, on_delete=models.CASCADE)
    recording_url   = models.URLField()
    transcript      = models.TextField(blank=True)
    ai_summary      = models.TextField(blank=True)
    listened        = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/aria/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/config/` | Manage Aria configuration |
| `GET/POST` | `/knowledge-base/` | Manage FAQ knowledge base |
| `POST` | `/twilio/voice/` | Twilio webhook — inbound call handler |
| `POST` | `/twilio/status/` | Twilio call status callback |
| `GET` | `/calls/` | List all call logs |
| `GET` | `/calls/today/` | Today's call summary |
| `GET` | `/calls/{id}/` | Call detail + transcript + summary |
| `GET` | `/voicemails/` | Unheard voicemails |
| `GET` | `/appointments/` | Appointments booked via Aria |
| `GET` | `/analytics/` | Call volume, intent breakdown, booking rate, spam rate |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| Voice Platform | Twilio Programmable Voice | 💲 $0.0085/min inbound |
| STT | Google Cloud Speech-to-Text | 💲 $0.016/min (free 60 min/mo) |
| TTS | Google Cloud Text-to-Speech | 💲 $0.016/1K chars (free 1M/mo) |
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash | ✅ FREE |
| Calendar | Google Calendar API | ✅ FREE |
| SMS | Twilio SMS | 💲 $0.0079/SMS |
| Task Queue | `django-apscheduler` | ✅ FREE |

```
pip install twilio google-cloud-speech google-cloud-texttospeech google-api-python-client django-apscheduler
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Twilio inbound, STT/TTS, greeting script, FAQ answering, call log + transcript | Weeks 1–6 |
| Phase 2 | Appointment booking (Google Calendar), after-call SMS, spam detection, voicemail | Weeks 7–12 |
| Phase 3 | Intelligent routing, multi-language support, call analytics dashboard, WhatsApp integration | Weeks 13–18 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | Calls/mo | Features |
|---|---|---|---|
| Intern | Free | 30 | Basic call handling, FAQ |
| Entry | ৳2,000 | 150 | Appointment booking, call log |
| Mid | ৳5,000 | 500 | Spam filter, SMS, voicemail, analytics |
| Senior | ৳10,000 | Unlimited | Multi-language, routing, full dashboard |

---
*BengalBound HUB — dev branch*
