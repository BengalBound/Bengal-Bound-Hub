# Bengal Bound — Scout Agent

## Purpose
Scout is the Competitor Intelligence AI employee. It tracks competitor pricing, product launches, and hiring signals in real time — 24/7 monitoring.

## Phase
Phase 3

## File Structure
```
scout/
├── __init__.py
├── apps.py
├── models.py          # Competitor, CompetitorChange
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `Competitor`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| name | CharField | Competitor name |
| website | URLField | Website URL |
| pricing_url | URLField | Pricing page (optional) |
| linkedin_url | URLField | LinkedIn (optional) |
| twitter_handle | CharField | Twitter handle (optional) |
| is_active | BooleanField | Active monitoring flag |
| last_checked | DateTimeField | Last check timestamp |

### `CompetitorChange`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| competitor | FK | Parent Competitor |
| change_type | CharField | pricing / product / hiring / ad / content / pr |
| impact | CharField | low / medium / high |
| description | TextField | What changed |
| ai_analysis | TextField | AI strategic impact analysis |
| source_url | URLField | Source of the change |
| alert_sent | BooleanField | Alert notification flag |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/scout/competitors/` | List competitors |
| POST | `/api/v1/scout/competitors/` | Add competitor |
| GET | `/api/v1/scout/changes/` | List competitor changes |
| POST | `/api/v1/scout/changes/` | Log a change |
| POST | `/api/v1/scout/changes/{id}/analyse/` | **AI @action** — analyse impact |

## AI @Action

### `analyse` on `CompetitorChange`
Calls `ai_chat()` with change_type + description + competitor context. Writes `ai_analysis`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `scout`
- **Channels**: `chat`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/scout/competitors/
```
