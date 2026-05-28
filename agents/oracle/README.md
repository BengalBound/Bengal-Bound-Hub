# Bengal Bound — Oracle Agent

## Purpose
Oracle is the SEO Specialist AI employee. It audits sites, researches keywords, and fixes on-page issues automatically — driving Page 1 rankings.

## Phase
Phase 3

## File Structure
```
oracle/
├── __init__.py
├── apps.py
├── models.py          # Website, SEOIssue
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `Website`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| domain | URLField | Website domain |
| cms | CharField | CMS platform (optional) |
| last_crawled | DateTimeField | Last audit timestamp |

### `SEOIssue`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| website | FK | Parent Website |
| issue_type | CharField | missing_meta / broken_link / duplicate_content / slow_page / missing_schema / mobile_issue / missing_alt |
| severity | CharField | critical / warning / info |
| page_url | URLField | Affected page |
| description | TextField | Issue description |
| fix_suggestion | TextField | AI-generated fix |
| status | CharField | open / fixed / ignored |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/oracle/websites/` | List websites |
| POST | `/api/v1/oracle/websites/` | Add website |
| POST | `/api/v1/oracle/websites/{id}/audit/` | **AI @action** — run SEO audit |
| GET | `/api/v1/oracle/issues/` | List SEO issues |
| PATCH | `/api/v1/oracle/issues/{id}/` | Mark fixed/ignored |
| POST | `/api/v1/oracle/issues/{id}/fix/` | **AI @action** — generate fix |

## AI @Actions

### `audit` on `Website`
Calls `ai_chat()` to generate a mock audit. Creates `SEOIssue` records. Creates `AuditLog` entry.

### `fix` on `SEOIssue`
Calls `ai_chat()` with issue_type + description. Writes `fix_suggestion`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `oracle`
- **Channels**: `chat`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/oracle/websites/
```
