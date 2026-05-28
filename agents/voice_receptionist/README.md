# Bengal Bound — Voice Receptionist Agent

## Purpose
The Voice Receptionist is the Phone AI employee. It answers every inbound call, books appointments, takes messages, and routes to the right person — every call answered, 24/7.

## Phase
Phase 1 (live)

## File Structure
```
voice_receptionist/
├── __init__.py
├── apps.py                          ← AppConfig; starts APScheduler on boot
├── models.py                        ← 7 Django ORM models
├── admin.py                         ← Django Admin for all 7 models
├── ai_engine.py                     ← NLU intent extraction
├── google_voice.py                  ← Google Cloud TTS + STT wrappers
├── calendar_sync.py                 ← Google Calendar OAuth2 + event CRUD
├── notifications.py                 ← Twilio SMS + email notification service
├── spam_filter.py                   ← Multi-layer spam detection pipeline
├── scheduler.py                     ← APScheduler background jobs
├── analytics.py                     ← Django ORM analytics queries
├── twilio_handler.py                ← Twilio call flow state machine
├── auth.py                          ← Firebase JWT DRF authentication
├── permissions.py                   ← Role-based DRF permission classes
├── serializers.py                   ← All DRF serializers
├── views.py                         ← All DRF ViewSets + webhook views
├── urls.py                          ← Router + Twilio webhook URLs
├── settings_snippet.py              ← Settings reference block
├── requirements_voice.txt           ← Additional pip packages
├── .env.example                     ← All required environment variables
├── management/
│   └── commands/
│       └── update_spam_blocklist.py ← python manage.py update_spam_blocklist
├── migrations/
│   └── __init__.py
└── tests/
    ├── test_models.py
    ├── test_spam_filter.py
    ├── test_ai_engine.py
    └── test_api_endpoints.py
```

## Models

| Model | Purpose |
|-------|---------|
| `BusinessProfile` | Organisation's voice AI configuration (greeting, TTS voice, hours) |
| `CallLog` | Every inbound call with transcript, intent, outcome |
| `Appointment` | Booked appointments with status lifecycle |
| `SpamEntry` | Spam/robocall detection records |
| `CalendarToken` | Encrypted Google Calendar OAuth2 tokens |
| `UserProfile` | Extended user profile with role |
| `NotificationLog` | SMS / email notification delivery log |

## API Endpoints

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET/PUT/DELETE | `/api/v1/voice/profile/{id}/` | Admin | Business profile CRUD |
| GET | `/api/v1/voice/profile/voices/` | Any | List available TTS voices |
| GET | `/api/v1/voice/calls/` | Admin/Manager | Full call log |
| GET | `/api/v1/voice/calls/active/` | Admin/Manager | Live call feed |
| GET/POST/PUT/DELETE | `/api/v1/voice/appointments/` | Admin/Manager | Appointment CRUD |
| GET | `/api/v1/voice/appointments/upcoming/` | Admin/Manager | Next 7 days |
| GET | `/api/v1/voice/appointments/available_slots/` | Admin/Manager | Open slots |
| GET/PATCH | `/api/v1/voice/spam/` | Admin | Spam log + whitelist/blacklist |
| GET | `/api/v1/voice/analytics/?range=30` | Admin/Manager | Analytics summary |
| GET/POST | `/api/v1/voice/calendar/connect/` | Admin | Google Calendar OAuth |
| POST | `/api/v1/voice/webhook/inbound/` | Twilio sig | Inbound call entry point |
| POST | `/api/v1/voice/webhook/gather/` | Twilio sig | Speech recognition loop |
| POST | `/api/v1/voice/webhook/voicemail/` | Twilio sig | Voicemail recording |
| POST | `/api/v1/voice/webhook/transfer-complete/` | Twilio sig | Transfer outcome |

## AI Engine (`ai_engine.py`)
- Calls `core.ai_provider.ai_chat()` for intent extraction from call transcripts
- Intents: `book_appointment`, `get_info`, `leave_message`, `transfer`, `spam`
- All intent calls create `compliance.AuditLog` entries

## Channel Integration
- **WebSocket chat**: `ws://<host>/ws/chat/<session_id>/`
- **Agent slug**: `voice_receptionist`
- **Channels**: `voice`, `chat`, `api`
- Routes via `DEPARTMENT_ROUTES["voice"]` → `voice_receptionist` in `channels_comm/router.py`

## Running Locally

```bash
cd api
python manage.py migrate
python manage.py runserver

# Expose for Twilio webhook testing (use ngrok or similar):
# ngrok http 8000
# Set Twilio webhook to: https://<ngrok-url>/api/v1/voice/webhook/inbound/
```

## Environment Variables

```env
# Twilio
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=xxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx

# Google Cloud (TTS, STT, Calendar)
GOOGLE_CLOUD_PROJECT=your-project
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# AI Engine
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b
```

## Running Tests

```bash
cd api
python manage.py test agents.voice_receptionist --verbosity=2
```

## Twilio Webhook Setup

In your Twilio console, set the incoming call webhook URL:
```
https://your-domain.com/api/v1/voice/webhook/inbound/
```

## Agent Context
- All AI actions logged to `compliance.AuditLog`
- Inspector middleware validates all mutating requests
- Multi-tenant: all data scoped to `BusinessProfile.organization`
