# Bengal Bound — Content Architect Agent

## Purpose
Content Architect is the Editorial Planner AI employee. It builds content calendars, aligns campaigns to goals, and manages multi-channel publishing — a full content calendar in 1 hour.

## Phase
Phase 2

## File Structure
```
content_architect/
├── __init__.py
├── apps.py
├── models.py          # ContentCalendar, CalendarEntry
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `ContentCalendar`
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| organization | FK | Multi-tenant scope |
| name | CharField | Calendar name |
| goal | TextField | Campaign goal |
| month | DateField | Month (YYYY-MM-01) |
| status | CharField | draft / active / completed |

### `CalendarEntry`
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| calendar | FK | Parent ContentCalendar |
| title | CharField | Entry title |
| channel | CharField | blog / email / social / video / ad |
| publish_date | DateField | Target publish date |
| brief | TextField | Content brief |
| generated_content | TextField | AI output |
| status | CharField | planned / generated / approved / published |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/architect/calendars/` | List content calendars |
| POST | `/api/v1/architect/calendars/` | Create calendar |
| GET | `/api/v1/architect/entries/` | List calendar entries |
| POST | `/api/v1/architect/entries/` | Create entry |
| POST | `/api/v1/architect/entries/{id}/generate/` | **AI @action** — generate content |

## AI @Action

### `generate` on `CalendarEntry`
Calls `ai_chat()` with `brief` + channel context. Writes `generated_content`, sets status to `generated`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `content_architect`
- **Channels**: `chat`, `api`
- Routes via `DEPARTMENT_ROUTES["content"]` and `DEPARTMENT_ROUTES["editorial"]`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/architect/calendars/
```
