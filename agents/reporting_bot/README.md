# Bengal Bound — Reporting Bot Agent

## Purpose
Reporting Bot is the Automated Reporting AI employee. It generates scheduled reports, KPI summaries, and data narratives automatically — instant KPI reports on demand.

## Phase
Phase 3

## File Structure
```
reporting_bot/
├── __init__.py
├── apps.py
├── models.py          # ReportConfig, Report
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `ReportConfig`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| report_name | CharField | Report name |
| frequency | CharField | weekly / biweekly / monthly |
| send_day | CharField | Day to send (e.g. "monday") |
| recipients | JSONField | List of email addresses |
| data_sources | JSONField | Data source references |
| kpis | JSONField | KPI definitions |
| is_active | BooleanField | Schedule active flag |

### `Report`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| config | FK | Parent ReportConfig |
| period_start | DateField | Report start date |
| period_end | DateField | Report end date |
| ai_narrative | TextField | AI-generated narrative |
| status | CharField | generating / ready / sent / failed |
| generated_at | DateTimeField | Generation timestamp |
| sent_at | DateTimeField | Send timestamp |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/reporting/configs/` | List report configs |
| POST | `/api/v1/reporting/configs/` | Create config |
| GET | `/api/v1/reporting/reports/` | List reports |
| POST | `/api/v1/reporting/reports/` | Create report |
| POST | `/api/v1/reporting/reports/{id}/generate/` | **AI @action** — generate narrative |

## AI @Action

### `generate` on `Report`
Calls `ai_chat()` with KPI data + period. Writes `ai_narrative`. Sets status to `ready`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `reporting_bot`
- **Channels**: `chat`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/reporting/configs/
```
