# Bengal Bound — Sage Agent

## Purpose
Sage is the Legal Reviewer AI employee. It reviews contracts, flags risky clauses, and delivers plain-English risk summaries — 40+ risk checks per document.

## Phase
Phase 3

## File Structure
```
sage/
├── __init__.py
├── apps.py
├── models.py          # LegalDocument, Clause
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `LegalDocument`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| name | CharField | Document name |
| document_type | CharField | nda / contract / employment / vendor / compliance / other |
| raw_text | TextField | Full document text |
| overall_risk | IntegerField | 0-100 risk score |
| risk_label | CharField | low / medium / high / critical |
| executive_summary | TextField | AI plain-English summary |
| status | CharField | queued / reviewing / completed / failed |
| reviewed_at | DateTimeField | Review completion timestamp |

### `Clause`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| document | FK | Parent LegalDocument |
| clause_number | CharField | Clause reference |
| clause_title | CharField | Clause title |
| original_text | TextField | Raw clause text |
| plain_english | TextField | AI plain-English explanation |
| risk_level | CharField | safe / caution / risky / critical |
| risk_score | IntegerField | 0-100 risk score |
| negotiation_suggestion | TextField | AI negotiation advice |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/sage/documents/` | List legal documents |
| POST | `/api/v1/sage/documents/` | Upload document |
| POST | `/api/v1/sage/documents/{id}/review/` | **AI @action** — full document review |
| GET | `/api/v1/sage/documents/{id}/clauses/` | List clauses for document |
| POST | `/api/v1/sage/clauses/{id}/explain/` | **AI @action** — explain clause |

## AI @Actions

### `review` on `LegalDocument`
Calls `ai_chat()` with raw_text + document_type. Writes `executive_summary`, `overall_risk`, `risk_label`. Creates `Clause` records. Sets status to `completed`. Creates `AuditLog` entry.

### `explain` on `Clause`
Calls `ai_chat()` with original_text. Writes `plain_english` and `negotiation_suggestion`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `sage`
- **Channels**: `chat`, `api`
- Routes via `DEPARTMENT_ROUTES["legal"]` → `sage`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/sage/documents/
```
