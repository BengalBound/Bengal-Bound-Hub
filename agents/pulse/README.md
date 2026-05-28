# Bengal Bound — Pulse Agent

## Purpose
Pulse is the Market Researcher AI employee. It delivers competitive intelligence, trend analysis, and strategic opportunity maps from 20+ sources.

## Phase
Phase 3

## File Structure
```
pulse/
├── __init__.py
├── apps.py
├── models.py          # ResearchConfig, ResearchReport
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `ResearchConfig`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| industry | CharField | Target industry |
| keywords | JSONField | Tracking keywords |
| competitors | JSONField | Competitor names/URLs |
| target_markets | JSONField | Target market list |
| alert_threshold | IntegerField | Alert sensitivity (0-100) |

### `ResearchReport`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| period | CharField | Reporting period label |
| narrative | TextField | AI market narrative |
| key_findings | JSONField | List of findings |
| opportunities | JSONField | Market opportunities |
| threats | JSONField | Competitive threats |
| recommendations | JSONField | Strategic recommendations |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/pulse/configs/` | List research configs |
| POST | `/api/v1/pulse/configs/` | Create config |
| GET | `/api/v1/pulse/reports/` | List reports |
| POST | `/api/v1/pulse/reports/` | Create report |
| POST | `/api/v1/pulse/reports/{id}/generate/` | **AI @action** — generate market report |

## AI @Action

### `generate` on `ResearchReport`
Calls `ai_chat()` with industry + keywords + competitors. Writes `narrative`, `key_findings`, `opportunities`, `threats`, `recommendations`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `pulse`
- **Channels**: `chat`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/pulse/configs/
```
