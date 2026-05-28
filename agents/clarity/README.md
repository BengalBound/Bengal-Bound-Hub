# Bengal Bound — Clarity Agent

## Purpose
Clarity is the Feedback Analyst AI employee. It analyses survey responses, extracts themes, and surfaces actionable insights in seconds.

## Phase
Phase 3

## File Structure
```
clarity/
├── __init__.py
├── apps.py
├── models.py          # FeedbackSurvey, InsightTheme
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `FeedbackSurvey`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| name | CharField | Survey name |
| survey_type | CharField | in_app / post_session / nps / feature / exit |
| questions | JSONField | List of question objects |
| is_active | BooleanField | Active flag |
| responses_count | IntegerField | Running total |

### `InsightTheme`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| theme | CharField | Theme label |
| theme_type | CharField | pain_point / feature_request / praise / confusion |
| mention_count | IntegerField | How often this theme appears |
| priority_score | IntegerField | AI-calculated priority |
| example_quotes | JSONField | Representative quotes |
| ai_analysis | TextField | AI narrative |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/clarity/surveys/` | List surveys |
| POST | `/api/v1/clarity/surveys/` | Create survey |
| GET | `/api/v1/clarity/themes/` | List insight themes |
| POST | `/api/v1/clarity/themes/` | Create theme |
| POST | `/api/v1/clarity/themes/{id}/analyse/` | **AI @action** — deepen analysis |

## AI @Action

### `analyse` on `InsightTheme`
Calls `ai_chat()` with theme + example_quotes. Writes `ai_analysis` and updates `priority_score`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `clarity`
- **Channels**: `chat`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/clarity/surveys/
```
