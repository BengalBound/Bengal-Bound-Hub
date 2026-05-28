# Bengal Bound — Realt Agent

## Purpose
Realt is the Real Estate Agent AI employee. It manages listings, qualifies buyer and seller leads, and analyses market data — leads qualified instantly.

## Phase
Phase 3

## File Structure
```
realt/
├── __init__.py
├── apps.py
├── models.py          # Property, Lead
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `Property`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| title | CharField | Property title |
| property_type | CharField | apartment / house / commercial / land / office |
| listing_type | CharField | sale / rent |
| price | DecimalField | Asking price |
| area_sqft | IntegerField | Area in sq ft |
| bedrooms | IntegerField | Bedroom count (nullable) |
| location | CharField | Location description |
| description | TextField | Raw description |
| ai_description | TextField | AI-optimised listing |
| status | CharField | available / viewing / under_offer / sold / rented |

### `Lead`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| name | CharField | Lead name |
| phone | CharField | Lead phone |
| email | EmailField | Lead email (optional) |
| intent | CharField | buy / rent |
| budget_max | DecimalField | Maximum budget |
| preferred_areas | JSONField | Preferred locations |
| bedrooms_needed | IntegerField | Bedroom requirement |
| ai_score | IntegerField | AI qualification score |
| ai_notes | TextField | AI qualification notes |
| status | CharField | new / contacted / qualified / viewing / closed / lost |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/realt/properties/` | List properties |
| POST | `/api/v1/realt/properties/` | Add property |
| POST | `/api/v1/realt/properties/{id}/describe/` | **AI @action** — generate listing |
| GET | `/api/v1/realt/leads/` | List leads |
| POST | `/api/v1/realt/leads/` | Add lead |
| POST | `/api/v1/realt/leads/{id}/qualify/` | **AI @action** — qualify lead |

## AI @Actions

### `describe` on `Property`
Calls `ai_chat()` with property details. Writes `ai_description`. Creates `AuditLog` entry.

### `qualify` on `Lead`
Calls `ai_chat()` with intent + budget + preferences. Writes `ai_notes` and `ai_score`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `realt`
- **Channels**: `chat`, `voice`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/realt/properties/
```
