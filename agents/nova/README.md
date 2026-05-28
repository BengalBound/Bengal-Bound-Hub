# Bengal Bound — Nova Agent

## Purpose
Nova is the Data Analyst AI employee. It translates plain-English questions into SQL queries and delivers instant analysis — real-time insights on demand.

## Phase
Phase 2

## File Structure
```
nova/
├── __init__.py
├── apps.py
├── models.py          # DataSource, DataQuery
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `DataSource`
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| organization | FK | Multi-tenant scope |
| name | CharField | Source name |
| source_type | CharField | postgres / mysql / sheets / api / csv |
| connection_config | JSONField | Connection details (encrypted in prod) |
| is_active | BooleanField | Active flag |

### `DataQuery`
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| organization | FK | Multi-tenant scope |
| data_source | FK | Source (optional) |
| question | TextField | Natural-language question |
| generated_sql | TextField | AI-generated SQL |
| results_preview | JSONField | Sample results |
| status | CharField | pending / completed / failed |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/nova/sources/` | List data sources |
| POST | `/api/v1/nova/sources/` | Add data source |
| GET | `/api/v1/nova/queries/` | List queries |
| POST | `/api/v1/nova/queries/` | Create query |
| POST | `/api/v1/nova/queries/{id}/execute/` | **AI @action** — translate + execute |

## AI @Action

### `execute` on `DataQuery`
Calls `ai_chat()` with question + source_type context. Writes `generated_sql` and mock `results_preview`. Sets status to `completed`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `nova`
- **Channels**: `chat`, `api`
- Routes via `DEPARTMENT_ROUTES["data"]` → `nova`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl -X POST http://localhost:8000/api/v1/nova/queries/ \
  -H "Content-Type: application/json" \
  -d '{"question": "How many orders were placed last month?"}'
```

## Security Note
`connection_config` stores credentials. In production, encrypt this field or reference a secrets manager. Never log raw connection configs in `AuditLog`.
