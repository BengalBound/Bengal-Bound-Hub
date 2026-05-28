# Bengal Bound — Hera Agent

## Purpose
Hera is the HR Agent AI employee. She answers HR policy questions, handles onboarding tasks, and manages leave requests — infinite policies answered.

## Phase
Phase 2

## File Structure
```
hera/
├── __init__.py
├── apps.py
├── models.py          # PolicyQuery, OnboardingTask
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `PolicyQuery`
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| organization | FK | Multi-tenant scope |
| user | FK | Auth user (optional) |
| question | TextField | Employee's question |
| ai_answer | TextField | AI-generated response |
| category | CharField | onboarding / leave / benefits / conduct / payroll / other |

### `OnboardingTask`
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| organization | FK | Multi-tenant scope |
| employee_name | CharField | New hire name |
| employee_email | EmailField | New hire email |
| task | CharField | Task description |
| due_date | DateField | Nullable deadline |
| is_completed | BooleanField | Completion flag |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/hera/queries/` | List policy queries |
| POST | `/api/v1/hera/queries/` | Submit a question |
| POST | `/api/v1/hera/queries/{id}/answer/` | **AI @action** — generate answer |
| GET | `/api/v1/hera/onboarding/` | List onboarding tasks |
| POST | `/api/v1/hera/onboarding/` | Create task |
| PATCH | `/api/v1/hera/onboarding/{id}/` | Update task (mark complete) |

## AI @Action

### `answer` on `PolicyQuery`
Calls `ai_chat()` with question + category context. Writes `ai_answer`. Creates `AuditLog` entry.

## Channel Integration
- **WebSocket chat**: `ws://<host>/ws/chat/<session_id>/`
- **Agent slug**: `hera`
- **Channels**: `chat`, `widget`, `email`, `api`
- Routes via `DEPARTMENT_ROUTES["hr"]` → `hera`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl -X POST http://localhost:8000/api/v1/hera/queries/ \
  -H "Content-Type: application/json" \
  -d '{"question": "How many days of annual leave do I get?", "category": "leave"}'
```
