# Bengal Bound — Kai Agent

## Purpose
Kai is the DevOps Engineer AI employee. It monitors pipelines, analyzes incidents with AI root-cause analysis, and keeps production running — self-healing infrastructure.

## Phase
Phase 2

## File Structure
```
kai/
├── __init__.py
├── apps.py
├── models.py          # Pipeline, Incident
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `Pipeline`
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| organization | FK | Multi-tenant scope |
| name | CharField | Pipeline name |
| repo_url | URLField | Repository URL |
| provider | CharField | github / gitlab / bitbucket |
| last_status | CharField | passing / failing / unknown |
| last_run_at | DateTimeField | Last run timestamp |

### `Incident`
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| organization | FK | Multi-tenant scope |
| pipeline | FK | Related Pipeline (optional) |
| title | CharField | Incident title |
| severity | CharField | low / medium / high / critical |
| status | CharField | open / investigating / resolved |
| description | TextField | Incident description |
| ai_root_cause | TextField | AI root cause analysis |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/kai/pipelines/` | List pipelines |
| POST | `/api/v1/kai/pipelines/` | Add pipeline |
| PATCH | `/api/v1/kai/pipelines/{id}/` | Update pipeline status |
| GET | `/api/v1/kai/incidents/` | List incidents |
| POST | `/api/v1/kai/incidents/` | Create incident |
| POST | `/api/v1/kai/incidents/{id}/analyze/` | **AI @action** — root cause analysis |

## AI @Action

### `analyze` on `Incident`
Calls `ai_chat()` with title + description + severity. Writes `ai_root_cause`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `kai`
- **Channels**: `chat`, `api`
- Routes via `DEPARTMENT_ROUTES["devops"]` → `kai`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/kai/pipelines/
```
