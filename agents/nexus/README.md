# Bengal Bound — Nexus Agent

## Purpose
Nexus is the L&D Specialist AI employee. It creates course content, structures learning paths, and manages knowledge bases — full courses built in hours.

## Phase
Phase 3

## File Structure
```
nexus/
├── __init__.py
├── apps.py
├── models.py          # Course, Enrollment
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `Course`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| title | CharField | Course title |
| course_type | CharField | onboarding / technical / compliance / soft_skills |
| description | TextField | Course overview |
| modules | JSONField | List of module objects |
| duration_hours | FloatField | Estimated hours |
| is_mandatory | BooleanField | Required flag |
| ai_generated | BooleanField | True if AI authored |

### `Enrollment`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| course | FK | Parent Course |
| employee_name | CharField | Learner name |
| employee_email | EmailField | Learner email |
| status | CharField | assigned / in_progress / completed / overdue |
| progress_pct | IntegerField | 0-100 completion % |
| quiz_score | FloatField | Quiz score (nullable) |
| due_date | DateField | Completion deadline |
| completed_at | DateTimeField | Completion timestamp |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/nexus/courses/` | List courses |
| POST | `/api/v1/nexus/courses/` | Create course |
| POST | `/api/v1/nexus/courses/{id}/generate/` | **AI @action** — generate course content |
| GET | `/api/v1/nexus/enrollments/` | List enrollments |
| POST | `/api/v1/nexus/enrollments/` | Enroll learner |
| PATCH | `/api/v1/nexus/enrollments/{id}/` | Update progress |

## AI @Action

### `generate` on `Course`
Calls `ai_chat()` with title + course_type + description. Writes `modules` list and sets `ai_generated=True`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `nexus`
- **Channels**: `chat`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/nexus/courses/
```
