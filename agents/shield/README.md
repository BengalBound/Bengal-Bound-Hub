# Bengal Bound — Shield Agent

## Purpose
Shield is the IT Helpdesk AI employee. It handles Tier-1 IT tickets, auto-resolves common issues, and escalates edge cases — 80% auto-resolved.

## Phase
Phase 3

## File Structure
```
shield/
├── __init__.py
├── apps.py
├── models.py          # ITTicket, KnowledgeArticle
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `ITTicket`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| submitted_by | CharField | Employee name |
| title | CharField | Issue title |
| description | TextField | Full description |
| category | CharField | hardware / software / network / access / email / other |
| priority | CharField | low / medium / high / critical |
| status | CharField | open / ai_resolving / escalated / resolved / closed |
| ai_solution | TextField | AI-generated fix |
| ai_confidence | FloatField | Confidence score (0-1) |
| sla_hours | IntegerField | SLA target in hours |
| sla_breached | BooleanField | SLA breach flag |
| resolved_at | DateTimeField | Resolution timestamp |

### `KnowledgeArticle`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| title | CharField | Article title |
| category | CharField | Issue category |
| problem | TextField | Problem description |
| solution | TextField | Resolution steps |
| success_count | IntegerField | Times used successfully |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/shield/tickets/` | List IT tickets |
| POST | `/api/v1/shield/tickets/` | Submit ticket |
| POST | `/api/v1/shield/tickets/{id}/resolve/` | **AI @action** — auto-resolve |
| PATCH | `/api/v1/shield/tickets/{id}/` | Escalate / close |
| GET | `/api/v1/shield/knowledge/` | List KB articles |
| POST | `/api/v1/shield/knowledge/` | Add KB article |

## AI @Action

### `resolve` on `ITTicket`
Calls `ai_chat()` with category + description. Writes `ai_solution` and `ai_confidence`. Sets status to `ai_resolving`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `shield`
- **Channels**: `chat`, `widget`, `api`
- Routes via `DEPARTMENT_ROUTES["it"]` → `shield`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/shield/tickets/
```
