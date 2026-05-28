# Module Requirements: Merch — AI E-commerce Manager
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `merch` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Shopify API, WooCommerce REST API, Daraz Seller API, Facebook Shops, inventory webhooks

---

## Section 1: Overview

**AI Employee Name:** Merch | **Department:** E-commerce Operations
**Target Clients:** E-commerce brands, Daraz sellers, Shopify store owners, and multi-platform retailers.
**Core Function:** Monitors inventory, updates product listings, handles order tracking queries, identifies best-selling trends, and auto-adjusts pricing based on competitor and demand data.
**Value Prop:** *"Your store runs itself. Stock alerts, price wins, and listing updates — handled automatically."*

| | Human E-commerce Manager | Merch AI |
|---|---|---|
| Monthly Cost | ৳25,000–৳40,000 | ৳2,000 |
| Price Monitoring | Weekly manual checks | Real-time automated |
| Listing Updates | Hours per SKU | Seconds per SKU |
| Order Query Handling | Manual replies | Instant automated |

---

## Section 2: Core Capabilities

1. **Inventory Monitor** — Real-time stock level tracking; alerts when SKU drops below reorder threshold; auto-generates purchase orders
2. **AI Product Listing Generator** — Gemini writes SEO-optimized titles, descriptions, and bullet points for new products
3. **Dynamic Pricing** — Monitors competitor prices and demand trends; adjusts pricing within client-set min/max bounds automatically
4. **Order Support Bot** — WhatsApp/chat bot handles "where is my order" queries with live tracking data
5. **Sales Trend Analyzer** — Weekly report on best-sellers, slow-movers, seasonal trends, and recommended promotional products
6. **Review Response Automation** — AI drafts responses to customer reviews on all platforms
7. **Low-Stock Reorder Alerts** — When stock threshold hit, auto-generates email to supplier with purchase order details

---

## Section 3: Django Models

```python
class Store(models.Model):
    PLATFORMS = [('shopify','Shopify'),('woocommerce','WooCommerce'),
                 ('daraz','Daraz'),('facebook','Facebook Shops'),('custom','Custom')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='merch_stores')
    platform        = models.CharField(max_length(20), choices=PLATFORMS)
    store_name      = models.CharField(max_length(300))
    api_key         = models.TextField()               # Encrypted
    api_secret      = models.TextField(blank=True)
    store_url       = models.URLField(blank=True)
    currency        = models.CharField(max_length(10), default='BDT')
    is_active       = models.BooleanField(default=True)
    last_synced     = models.DateTimeField(null=True)

class Product(models.Model):
    store           = models.ForeignKey(Store, on_delete=models.CASCADE)
    external_id     = models.CharField(max_length(200))
    title           = models.CharField(max_length(500))
    sku             = models.CharField(max_length(100), blank=True)
    price           = models.DecimalField(max_digits=12, decimal_places=2)
    ai_price        = models.DecimalField(max_digits=12, decimal_places=2, null=True)  # AI-suggested
    stock_quantity  = models.IntegerField()
    reorder_threshold = models.IntegerField(default=10)
    is_low_stock    = models.BooleanField(default=False)
    category        = models.CharField(max_length(200), blank=True)
    description     = models.TextField(blank=True)
    ai_description  = models.TextField(blank=True)     # Gemini-generated
    last_sold_at    = models.DateTimeField(null=True)
    units_sold_30d  = models.IntegerField(default=0)
    last_synced     = models.DateTimeField(null=True)

class PriceHistory(models.Model):
    product         = models.ForeignKey(Product, on_delete=models.CASCADE)
    old_price       = models.DecimalField(max_digits=12, decimal_places=2)
    new_price       = models.DecimalField(max_digits=12, decimal_places=2)
    reason          = models.TextField()               # Gemini explanation
    changed_at      = models.DateTimeField(auto_now_add=True)
    reverted        = models.BooleanField(default=False)

class OrderQuery(models.Model):
    STATUS = [('resolved','Resolved'),('escalated','Escalated'),('pending','Pending')]
    store           = models.ForeignKey(Store, on_delete=models.CASCADE)
    order_id        = models.CharField(max_length(200))
    customer_name   = models.CharField(max_length(300))
    customer_contact = models.CharField(max_length(200))
    query           = models.TextField()
    ai_response     = models.TextField()
    status          = models.CharField(max_length(20), choices=STATUS, default='pending')
    created_at      = models.DateTimeField(auto_now_add=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/merch/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/stores/` | Connect and manage stores |
| `POST` | `/stores/{id}/sync/` | Force product/inventory sync |
| `GET` | `/products/` | List products with AI data |
| `GET` | `/products/low-stock/` | Products below reorder threshold |
| `POST` | `/products/{id}/generate-listing/` | AI-generate product description |
| `POST` | `/products/{id}/apply-ai-price/` | Apply AI-suggested price |
| `GET` | `/price-history/` | Pricing change log |
| `GET` | `/trends/` | Best-sellers, slow-movers, seasonal trends |
| `GET` | `/order-queries/` | Customer order queries |
| `POST` | `/order-queries/{id}/send-response/` | Send AI response |
| `GET` | `/analytics/` | Revenue, units sold, margin, stock turnover |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash | ✅ FREE |
| Shopify | `ShopifyAPI` Python library | ✅ FREE |
| WooCommerce | WooCommerce REST API (`woocommerce`) | ✅ FREE |
| Daraz | Daraz Open Platform API | ✅ FREE |
| WhatsApp | WhatsApp Business API | 💲 Per conversation |
| Task Queue | `django-apscheduler` | ✅ FREE |

```
pip install ShopifyAPI woocommerce requests django-apscheduler
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Shopify sync, inventory alerts, AI listing generator, basic dashboard | Weeks 1–6 |
| Phase 2 | Dynamic pricing, order query bot, sales trend report, WooCommerce support | Weeks 7–12 |
| Phase 3 | Daraz integration, review responses, multi-store dashboard, competitor price monitoring | Weeks 13–18 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | SKUs | Features |
|---|---|---|---|
| Intern | Free | 50 | Inventory monitor, dashboard |
| Entry | ৳2,000 | 200 | AI listings, price alerts |
| Mid | ৳5,000 | 1,000 | Dynamic pricing, order bot, trends |
| Senior | ৳10,000 | Unlimited | Multi-store, Daraz, review automation |

---
*BengalBound HUB — dev branch*
