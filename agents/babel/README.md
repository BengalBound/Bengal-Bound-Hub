# Bengal Bound — Babel Agent

## Purpose
Babel is the Translation Specialist AI employee. It translates documents and messages across 95 languages with domain-aware accuracy and tone preservation.

## Phase
Phase 3

## File Structure
```
babel/
├── __init__.py
├── apps.py
├── models.py          # TranslationJob, TranslationOutput
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `TranslationJob`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| source_language | CharField | ISO 639-1 code (e.g. "en") |
| target_languages | JSONField | List of target codes |
| source_text | TextField | Original text |
| word_count | IntegerField | Auto-calculated |
| status | CharField | queued / processing / completed / failed |
| completed_at | DateTimeField | Nullable |

### `TranslationOutput`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| job | FK | Parent TranslationJob |
| target_language | CharField | ISO 639-1 code |
| translated_text | TextField | Output |
| quality_score | FloatField | Nullable confidence (0-1) |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/babel/jobs/` | List translation jobs |
| POST | `/api/v1/babel/jobs/` | Create job |
| POST | `/api/v1/babel/jobs/{id}/translate/` | **AI @action** — run translation |
| GET | `/api/v1/babel/jobs/{id}/outputs/` | Get outputs for a job |

## AI @Action

### `translate` on `TranslationJob`
Calls `ai_chat()` for each target language. Creates `TranslationOutput` records. Sets status to `completed`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `babel`
- **Channels**: `chat`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/babel/jobs/
```
