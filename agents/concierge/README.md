# Bengal Bound — Concierge Agent

## Purpose
The Concierge is the front-door AI employee. It greets every visitor, triages inbound emails, qualifies meeting requests, and routes to the right team — across chat, widget, email, and API channels.

## Phase
Phase 1 (live)

## File Structure
```
concierge/
├── __init__.py
├── apps.py
├── models.py          # MeetingRequest, EmailTriage
├── serializers.py
├── views.py           # ViewSets + AI @actions
├── urls.py
├── admin.py
└── migrations/
```

## Models

### `MeetingRequest`
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| organization | FK | Multi-tenant scope |
| title | CharField | Meeting title |
| description | TextField | Details |
| attendees | JSONField | List of emails |
| preferred_times | JSONField | ISO-8601 datetime list |
| status | CharField | pending / scheduled / cancelled / completed |
| calendar_event_id | CharField | Google Calendar event ID |

### `EmailTriage`
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| organization | FK | Multi-tenant scope |
| sender | EmailField | From address |
| subject | CharField | Email subject |
| body_preview | TextField | First ~500 chars |
| category | CharField | inquiry / sales / support / complaint / newsletter / internal / spam / other |
| priority | CharField | low / medium / high / urgent |
| is_processed | BooleanField | Processing flag |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/concierge/meetings/` | List meeting requests |
| POST | `/api/v1/concierge/meetings/` | Create meeting request |
| POST | `/api/v1/concierge/meetings/{id}/schedule/` | **AI @action** — schedule + confirm |
| GET | `/api/v1/concierge/emails/` | List email triages |
| POST | `/api/v1/concierge/emails/` | Create email triage |
| POST | `/api/v1/concierge/emails/{id}/triage/` | **AI @action** — classify + prioritise |

## AI @Actions

### `schedule` on `MeetingRequest`
Calls `ai_chat()` to confirm timing, suggest slots, and update status to `scheduled`. Creates `AuditLog` entry.

### `triage` on `EmailTriage`
Calls `ai_chat()` to classify category and priority from subject + body_preview. Creates `AuditLog` entry.

## Channel Integration
- **WebSocket chat**: `ws://<host>/ws/chat/<session_id>/`
- **Agent slug**: `concierge`
- **Default channel**: `chat`, `widget`, `email`, `api`

## Running Locally
```bash
cd api
python manage.py migrate
python manage.py runserver
# Test:
curl http://localhost:8000/api/v1/concierge/meetings/
```

## Environment Variables
```
AI_PROVIDER=ollama          # or gemini / openai
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b
```

## Agent Context
- Routes inbound chat to concierge via `DEPARTMENT_ROUTES` in `channels_comm/router.py`
- All AI output is logged to `compliance.AuditLog`
- Inspector middleware validates every mutating request
