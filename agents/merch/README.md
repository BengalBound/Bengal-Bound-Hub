# Bengal Bound — Merch Agent

## Purpose
Merch is the eCommerce Manager AI employee. It optimises product listings, manages inventory, and analyses sales performance — listings optimised daily.

## Phase
Phase 3

## File Structure
```
merch/
├── __init__.py
├── apps.py
├── models.py          # Store, Product
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `Store`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| platform | CharField | shopify / woocommerce / daraz / facebook / custom |
| store_name | CharField | Store name |
| store_url | URLField | Store URL (optional) |
| currency | CharField | Default BDT |
| is_active | BooleanField | Active flag |

### `Product`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| store | FK | Parent Store |
| title | CharField | Product title |
| sku | CharField | SKU code |
| price | DecimalField | Current price |
| stock_quantity | IntegerField | Inventory count |
| reorder_threshold | IntegerField | Low-stock trigger (default 10) |
| is_low_stock | BooleanField | Auto-flagged |
| ai_description | TextField | AI-optimised listing description |
| ai_price | DecimalField | AI price recommendation |
| units_sold_30d | IntegerField | 30-day sales volume |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/merch/stores/` | List stores |
| POST | `/api/v1/merch/stores/` | Add store |
| GET | `/api/v1/merch/products/` | List products |
| POST | `/api/v1/merch/products/` | Add product |
| POST | `/api/v1/merch/products/{id}/optimise/` | **AI @action** — optimise listing |

## AI @Action

### `optimise` on `Product`
Calls `ai_chat()` with title + store platform + sales data. Writes `ai_description` and `ai_price`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `merch`
- **Channels**: `chat`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/merch/stores/
```
