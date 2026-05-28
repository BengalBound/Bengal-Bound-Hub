# Bengal Bound — Payload Agent

## Purpose
Payload is the Procurement Manager AI employee. It sources vendors, distributes RFQs, and evaluates bids with AI scoring — always the best price.

## Phase
Phase 3

## File Structure
```
payload/
├── __init__.py
├── apps.py
├── models.py          # Vendor, RFQ
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `Vendor`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| name | CharField | Vendor name |
| category | CharField | Procurement category |
| contact_name | CharField | Primary contact |
| contact_email | EmailField | Contact email |
| contact_phone | CharField | Phone (optional) |
| country | CharField | Country |
| payment_terms | CharField | Payment terms |
| performance_score | IntegerField | 0-100 score (nullable) |
| status | CharField | active / on_hold / blacklisted |

### `RFQ`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| title | CharField | RFQ title |
| description | TextField | Requirements description |
| requirements | JSONField | Specific requirement list |
| deadline | DateTimeField | Response deadline |
| status | CharField | draft / sent / responses_in / evaluated / awarded |
| ai_recommendation | TextField | AI vendor recommendation |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/payload/vendors/` | List vendors |
| POST | `/api/v1/payload/vendors/` | Add vendor |
| GET | `/api/v1/payload/rfqs/` | List RFQs |
| POST | `/api/v1/payload/rfqs/` | Create RFQ |
| POST | `/api/v1/payload/rfqs/{id}/evaluate/` | **AI @action** — evaluate bids |

## AI @Action

### `evaluate` on `RFQ`
Calls `ai_chat()` with requirements + vendor context. Writes `ai_recommendation`. Sets status to `evaluated`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `payload`
- **Channels**: `chat`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/payload/rfqs/
```
