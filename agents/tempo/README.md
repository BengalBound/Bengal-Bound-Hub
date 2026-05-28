# Bengal Bound — Tempo Agent

## Purpose
Tempo is the Events Manager AI employee. It plans events, manages attendees, coordinates logistics, and measures ROI — events run flawlessly.

## Phase
Phase 3

## File Structure
```
tempo/
├── __init__.py
├── apps.py
├── models.py          # Event, Attendee
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `Event`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| name | CharField | Event name |
| event_type | CharField | conference / workshop / product_launch / team_building / webinar / gala |
| date | DateTimeField | Event datetime |
| location | CharField | Venue / online link |
| expected_headcount | IntegerField | Expected attendee count |
| total_budget | DecimalField | Allocated budget |
| spent_so_far | DecimalField | Actual spend |
| status | CharField | planning / confirmed / live / completed / cancelled |
| ai_plan | TextField | AI-generated event plan |

### `Attendee`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| event | FK | Parent Event |
| name | CharField | Attendee name |
| email | EmailField | Attendee email |
| company | CharField | Attendee company (optional) |
| rsvp_status | CharField | pending / confirmed / declined / waitlist |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/tempo/events/` | List events |
| POST | `/api/v1/tempo/events/` | Create event |
| POST | `/api/v1/tempo/events/{id}/plan/` | **AI @action** — generate event plan |
| GET | `/api/v1/tempo/events/{id}/attendees/` | List attendees |
| POST | `/api/v1/tempo/attendees/` | Add attendee |
| PATCH | `/api/v1/tempo/attendees/{id}/` | Update RSVP |

## AI @Action

### `plan` on `Event`
Calls `ai_chat()` with event_type + headcount + budget + date. Writes `ai_plan` as a structured run-of-show. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `tempo`
- **Channels**: `chat`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/tempo/events/
```
