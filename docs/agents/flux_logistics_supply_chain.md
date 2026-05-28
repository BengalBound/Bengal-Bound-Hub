# Module Requirements: Flux — AI Logistics & Supply Chain Coordinator
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `flux` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)

---

## Section 1: Overview

**AI Employee Name:** Flux | **Department:** Operations / Supply Chain
**Core Function:** Tracks inventory, monitors supplier lead times, optimises reorder points, coordinates shipments, and sends real-time alerts on delays — keeping the supply chain running without a logistics manager watching it.
**Value Prop:** *"Never run out of stock. Never miss a shipment. Flux manages your supply chain 24/7."*

---

## Section 2: Core Capabilities

1. **Inventory Tracking** — Real-time stock levels across multiple warehouses/locations
2. **Reorder Intelligence** — AI calculates optimal reorder points based on historical demand, lead times, and safety stock
3. **Supplier Management** — Supplier registry with performance scores (on-time rate, quality, pricing)
4. **Shipment Tracking** — Integrates with shipping APIs (DHL, FedEx, local BD couriers) for live shipment status
5. **Delay Alerts** — Immediate notification when a shipment is delayed or a supplier misses a delivery deadline
6. **Purchase Order Generator** — Auto-generates POs when stock hits reorder point; sends to supplier for approval
7. **Demand Forecasting** — Predicts next-month stock requirements based on sales trends and seasonal patterns
8. **Cost Optimiser** — Suggests optimal order quantities (EOQ) and identifies cheaper supplier alternatives

---

## Section 3: Django Models

```python
class Warehouse(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='flux_warehouses')
    name            = models.CharField(max_length=300)
    location        = models.CharField(max_length(500))
    manager_name    = models.CharField(max_length(200), blank=True)
    manager_phone   = models.CharField(max_length(30), blank=True)
    is_active       = models.BooleanField(default=True)

class Product(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='flux_products')
    sku             = models.CharField(max_length=100)
    name            = models.CharField(max_length(500))
    unit            = models.CharField(max_length(50))    # 'pcs', 'kg', 'litre'
    reorder_point   = models.IntegerField()
    reorder_qty     = models.IntegerField()
    lead_time_days  = models.IntegerField(default=7)
    ai_reorder_point = models.IntegerField(null=True)     # AI-calculated
    ai_reorder_qty  = models.IntegerField(null=True)

class StockLevel(models.Model):
    product         = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse       = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity        = models.IntegerField()
    is_low          = models.BooleanField(default=False)
    updated_at      = models.DateTimeField(auto_now=True)

class Supplier(models.Model):
    RATING = [('excellent','Excellent'),('good','Good'),('average','Average'),('poor','Poor')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='flux_suppliers')
    name            = models.CharField(max_length=300)
    contact_email   = models.EmailField()
    contact_phone   = models.CharField(max_length=30)
    country         = models.CharField(max_length=100)
    on_time_rate    = models.FloatField(null=True)        # % of on-time deliveries
    avg_lead_days   = models.IntegerField(null=True)
    rating          = models.CharField(max_length=10, choices=RATING, blank=True)
    products        = models.ManyToManyField(Product, blank=True)

class PurchaseOrder(models.Model):
    STATUS = [('draft','Draft'),('sent','Sent to Supplier'),('confirmed','Confirmed'),
              ('shipped','Shipped'),('received','Received'),('overdue','Overdue')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='flux_purchaseorders')
    supplier        = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    po_number       = models.CharField(max_length=100, unique=True)
    expected_date   = models.DateField()
    total_value     = models.DecimalField(max_digits=14, decimal_places=2)
    status          = models.CharField(max_length=20, choices=STATUS, default='draft')
    tracking_number = models.CharField(max_length(200), blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    received_at     = models.DateTimeField(null=True)

class Shipment(models.Model):
    STATUS = [('in_transit','In Transit'),('delayed','Delayed'),
              ('delivered','Delivered'),('exception','Exception')]
    purchase_order  = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    carrier         = models.CharField(max_length(100))
    tracking_number = models.CharField(max_length(200))
    status          = models.CharField(max_length=20, choices=STATUS)
    estimated_delivery = models.DateField(null=True)
    last_location   = models.CharField(max_length(300), blank=True)
    delay_hours     = models.IntegerField(null=True)
    alert_sent      = models.BooleanField(default=False)
    last_updated    = models.DateTimeField(null=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/flux/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/warehouses/` | Manage warehouse locations |
| `GET/POST` | `/products/` | Product catalogue with stock |
| `GET` | `/stock/low/` | Products below reorder point |
| `GET/POST` | `/suppliers/` | Supplier registry |
| `GET` | `/suppliers/{id}/performance/` | Supplier scorecard |
| `POST` | `/purchase-orders/generate/` | Auto-generate PO for low stock |
| `GET` | `/purchase-orders/` | All POs + status |
| `GET` | `/shipments/` | Live shipment tracking |
| `GET` | `/shipments/delayed/` | Delayed shipments |
| `GET` | `/forecast/` | Next-month demand forecast |
| `GET` | `/analytics/` | Stockout events, supplier performance, cost trends |

---

## Section 5: Tech Stack & Delivery

```
pip install requests django-apscheduler reportlab
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Inventory tracking, reorder alerts, supplier registry, PO generator | Weeks 1–6 |
| Phase 2 | Shipment tracking (DHL/FedEx API), delay alerts, supplier scoring | Weeks 7–12 |
| Phase 3 | AI demand forecasting, cost optimiser, multi-warehouse, EOQ calculator | Weeks 13–18 |

| Tier | Monthly | Products | Features |
|---|---|---|---|
| Intern | Free | 50 | Stock tracking + alerts |
| Entry | ৳2,000 | 200 | PO generator, supplier mgmt |
| Mid | ৳5,000 | 1,000 | Shipment tracking, scoring |
| Senior | ৳10,000 | Unlimited | Forecasting, cost optimiser, multi-warehouse |

*BengalBound HUB — dev branch*
