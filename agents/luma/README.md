# Bengal Bound — Luma Agent

## Purpose
Luma is the Brand PR Manager AI employee. It monitors brand mentions, detects crises, and drafts press releases and media responses — crisis handled in minutes.

## Phase
Phase 3

## File Structure
```
luma/
├── __init__.py
├── apps.py
├── models.py          # BrandMention, PressRelease
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `BrandMention`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| source | CharField | news / twitter / reddit / review / blog / forum |
| url | URLField | Source URL |
| title | CharField | Article/post title |
| snippet | TextField | Relevant excerpt |
| sentiment | CharField | positive / neutral / negative |
| urgency | CharField | low / medium / high / crisis |
| ai_summary | TextField | AI analysis |
| response_draft | TextField | AI-drafted response |
| responded | BooleanField | Response sent flag |

### `PressRelease`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| headline | CharField | PR headline |
| body | TextField | Full release text |
| boilerplate | TextField | Standard company boilerplate |
| status | CharField | draft / approved / distributed |
| distributed_at | DateTimeField | Distribution timestamp |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/luma/mentions/` | List brand mentions |
| POST | `/api/v1/luma/mentions/` | Log mention |
| POST | `/api/v1/luma/mentions/{id}/respond/` | **AI @action** — draft response |
| GET | `/api/v1/luma/releases/` | List press releases |
| POST | `/api/v1/luma/releases/` | Create press release |
| POST | `/api/v1/luma/releases/{id}/generate/` | **AI @action** — generate release |

## AI @Actions

### `respond` on `BrandMention`
Calls `ai_chat()` with snippet + sentiment + urgency. Writes `response_draft` and `ai_summary`. Creates `AuditLog` entry.

### `generate` on `PressRelease`
Calls `ai_chat()` with headline + context. Writes full `body`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `luma`
- **Channels**: `chat`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/luma/mentions/
```
