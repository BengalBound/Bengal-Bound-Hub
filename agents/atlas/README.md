# Bengal Bound — Atlas Agent

## Purpose
Atlas is the Executive Assistant AI employee. It manages calendars, captures action items from meetings, prepares briefing documents, and ensures zero missed tasks.

## Phase
Phase 3

## File Structure
```
atlas/
├── __init__.py
├── apps.py
├── models.py          # ExecTask, MeetingBrief
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `ExecTask`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| title | CharField | Task title |
| description | TextField | Details |
| source | CharField | Origin (meeting / email / slack / manual) |
| priority | CharField | low / medium / high / urgent |
| status | CharField | open / in_progress / done / deferred |
| due_date | DateField | Nullable |
| completed_at | DateTimeField | Nullable |

### `MeetingBrief`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| meeting_title | CharField | Title |
| scheduled_at | DateTimeField | When the meeting is |
| attendees | JSONField | List of attendee names/emails |
| agenda | TextField | Raw agenda |
| talking_points | JSONField | AI-extracted list |
| ai_briefing | TextField | AI-generated executive brief |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/atlas/tasks/` | List exec tasks |
| POST | `/api/v1/atlas/tasks/` | Create task |
| PATCH | `/api/v1/atlas/tasks/{id}/` | Update task |
| GET | `/api/v1/atlas/briefs/` | List meeting briefs |
| POST | `/api/v1/atlas/briefs/` | Create brief |
| POST | `/api/v1/atlas/briefs/{id}/generate/` | **AI @action** — generate briefing |

## AI @Action

### `generate` on `MeetingBrief`
Calls `ai_chat()` with meeting title, agenda, attendees. Writes `talking_points` and `ai_briefing`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `atlas`
- **Channels**: `chat`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/atlas/tasks/
```
