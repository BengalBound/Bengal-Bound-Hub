# Bengal Bound — MediBook Agent

## Purpose
MediBook is the Medical Scheduler AI employee. It books appointments, coordinates patients and providers, and sends reminders — zero missed appointments.

## Phase
Phase 3

## File Structure
```
medibook/
├── __init__.py
├── apps.py
├── models.py          # Doctor, Appointment
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `Doctor`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| name | CharField | Doctor's full name |
| specialty | CharField | Medical specialty |
| email | EmailField | Doctor's email |
| phone | CharField | Phone (optional) |
| slot_duration | IntegerField | Minutes per slot (default 20) |
| is_active | BooleanField | Active flag |

### `Appointment`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| doctor | FK | Assigned Doctor |
| patient_name | CharField | Patient full name |
| patient_phone | CharField | Patient phone |
| patient_email | EmailField | Patient email (optional) |
| scheduled_at | DateTimeField | Appointment datetime |
| duration | IntegerField | Duration in minutes |
| reason | CharField | Visit reason |
| status | CharField | booked / confirmed / cancelled / rescheduled / completed / no_show |
| reminder_sent | BooleanField | Reminder flag |
| ai_notes | TextField | AI-generated appointment notes |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/medibook/doctors/` | List doctors |
| POST | `/api/v1/medibook/doctors/` | Add doctor |
| GET | `/api/v1/medibook/appointments/` | List appointments |
| POST | `/api/v1/medibook/appointments/` | Book appointment |
| PATCH | `/api/v1/medibook/appointments/{id}/` | Update status |
| POST | `/api/v1/medibook/appointments/{id}/notes/` | **AI @action** — generate notes |

## AI @Action

### `notes` on `Appointment`
Calls `ai_chat()` with patient reason + doctor specialty. Writes `ai_notes`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `medibook`
- **Channels**: `chat`, `voice`, `api`
- Routes via `DEPARTMENT_ROUTES["medical"]` and `DEPARTMENT_ROUTES["appointments"]`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/medibook/doctors/
```
