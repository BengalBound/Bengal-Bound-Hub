# Bengal Bound — Flux Agent

## Purpose
Flux is the Supply Chain Manager AI employee. It tracks inventory, scores suppliers, and generates purchase orders automatically — stock never runs out.

## Phase
Phase 3

## File Structure
```
flux/
├── __init__.py
├── apps.py
├── models.py          # Supplier, PurchaseOrder
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `Supplier`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| name | CharField | Supplier name |
| contact_email | EmailField | Primary contact |
| contact_phone | CharField | Phone (optional) |
| country | CharField | Country (optional) |
| on_time_rate | FloatField | Delivery on-time % |
| avg_lead_days | IntegerField | Average lead time |
| rating | CharField | excellent / good / average / poor |
| ai_summary | TextField | AI-generated supplier assessment |

### `PurchaseOrder`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| supplier | FK | Parent Supplier |
| po_number | CharField | PO reference |
| expected_date | DateField | Expected delivery |
| total_value | DecimalField | Total PO value |
| status | CharField | draft / sent / confirmed / shipped / received / overdue |
| items | JSONField | Line items list |
| ai_recommendation | TextField | AI sourcing recommendation |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/flux/suppliers/` | List suppliers |
| POST | `/api/v1/flux/suppliers/` | Add supplier |
| POST | `/api/v1/flux/suppliers/{id}/assess/` | **AI @action** — score supplier |
| GET | `/api/v1/flux/orders/` | List purchase orders |
| POST | `/api/v1/flux/orders/` | Create PO |
| POST | `/api/v1/flux/orders/{id}/recommend/` | **AI @action** — sourcing recommendation |

## AI @Actions

### `assess` on `Supplier`
Calls `ai_chat()` with supplier metrics. Writes `ai_summary` and updates `rating`. Creates `AuditLog` entry.

### `recommend` on `PurchaseOrder`
Calls `ai_chat()` with items + supplier context. Writes `ai_recommendation`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `flux`
- **Channels**: `chat`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/flux/suppliers/
```
