# Bengal Bound — Dox Agent

## Purpose
Dox is the Technical Writer AI employee. It generates clear API docs, user guides, SOPs, and references from code and specs — documentation auto-generated on demand.

## Phase
Phase 3

## File Structure
```
dox/
├── __init__.py
├── apps.py
├── models.py          # DocumentationProject, DocPage
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `DocumentationProject`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| name | CharField | Project name |
| doc_type | CharField | api / user_manual / sop / wiki / changelog / code_docs |
| repo_url | URLField | Source repo (optional) |
| description | TextField | Project description |
| is_active | BooleanField | Active flag |
| last_generated | DateTimeField | Last doc generation timestamp |

### `DocPage`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| project | FK | Parent DocumentationProject |
| title | CharField | Page title |
| slug | SlugField | URL-safe identifier |
| content | TextField | Page content (Markdown) |
| section | CharField | Section heading |
| status | CharField | draft / published / outdated / archived |
| ai_generated | BooleanField | True if AI wrote it |
| word_count | IntegerField | Character count |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/dox/projects/` | List documentation projects |
| POST | `/api/v1/dox/projects/` | Create project |
| GET | `/api/v1/dox/pages/` | List doc pages |
| POST | `/api/v1/dox/pages/` | Create page |
| POST | `/api/v1/dox/pages/{id}/generate/` | **AI @action** — generate page content |

## AI @Action

### `generate` on `DocPage`
Calls `ai_chat()` with project doc_type + page title + section context. Writes `content`, sets `ai_generated=True`, updates `word_count`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `dox`
- **Channels**: `chat`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/dox/projects/
```
