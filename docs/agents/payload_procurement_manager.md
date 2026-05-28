# Module Requirements: Payload — AI Procurement & Vendor Manager
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `payload` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)

---

## Section 1: Overview

**AI Employee Name:** Payload | **Department:** Procurement & Operations
**Core Function:** Manages vendor sourcing, RFQ (Request for Quotation) distribution, bid comparison, purchase approval workflows, contract renewals, and vendor performance scoring — automating the entire procurement cycle.
**Value Prop:** *"Source the best vendors, get the best prices, and never miss a contract renewal — automatically."*

---

## Section 2: Core Capabilities

1. **Vendor Registry** — Centralised database of all vendors with contact info, contracts, payment terms, and performance scores
2. **RFQ Automation** — Client defines requirement → Gemini drafts RFQ → auto-sent to shortlisted vendors
3. **Bid Comparison** — AI scores and ranks received quotations on price, quality, lead time, and vendor reliability
4. **Purchase Approval Workflow** — PO requests routed through configurable approval chain (e.g., team lead → finance → CEO for >৳50,000)
5. **Contract Management** — Stores all vendor contracts; alerts 60/30 days before renewal or expiry
6. **Vendor Performance Scoring** — Scores vendors monthly on: on-time delivery, invoice accuracy, quality complaints, responsiveness
7. **Spend Analytics** — Monthly breakdown of procurement spend by vendor, category, and department
8. **Preferred Vendor List** — AI recommends preferred vendors based on historical performance for each category

---

## Section 3: Django Models

```python
class Vendor(models.Model):
    STATUS = [('active','Active'),('on_hold','On Hold'),('blacklisted','Blacklisted')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='payload_vendors')
    name            = models.CharField(max_length=300)
    category        = models.CharField(max_length=200)
    contact_name    = models.CharField(max_length=300)
    contact_email   = models.EmailField()
    contact_phone   = models.CharField(max_length=30)
    country         = models.CharField(max_length=100)
    payment_terms   = models.CharField(max_length=100)
    performance_score = models.IntegerField(null=True)
    status          = models.CharField(max_length=20, choices=STATUS, default='active')
    registered_at   = models.DateTimeField(auto_now_add=True)

class RFQ(models.Model):
    STATUS = [('draft','Draft'),('sent','Sent'),('responses_in','Responses Received'),
              ('evaluated','Evaluated'),('awarded','Awarded')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='payload_rfqs')
    title           = models.CharField(max_length=500)
    description     = models.TextField()
    requirements    = models.JSONField(default=list)
    vendors_sent_to = models.ManyToManyField(Vendor, blank=True)
    deadline        = models.DateTimeField()
    status          = models.CharField(max_length=20, choices=STATUS, default='draft')
    awarded_to      = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True,
                                         blank=True, related_name='awarded_rfqs')
    created_at      = models.DateTimeField(auto_now_add=True)

class VendorQuote(models.Model):
    rfq             = models.ForeignKey(RFQ, on_delete=models.CASCADE)
    vendor          = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    amount          = models.DecimalField(max_digits=14, decimal_places=2)
    lead_time_days  = models.IntegerField()
    notes           = models.TextField(blank=True)
    ai_score        = models.IntegerField(null=True)      # AI ranking score 0–100
    ai_recommendation = models.TextField(blank=True)
    submitted_at    = models.DateTimeField()

class VendorContract(models.Model):
    STATUS = [('active','Active'),('expiring_soon','Expiring Soon'),('expired','Expired')]
    vendor          = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    contract_file   = models.FileField(upload_to='contracts/vendors/')
    start_date      = models.DateField()
    end_date        = models.DateField()
    value           = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    auto_renew      = models.BooleanField(default=False)
    renewal_alert_sent = models.BooleanField(default=False)
    status          = models.CharField(max_length=20, choices=STATUS, default='active')
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/payload/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/vendors/` | Vendor registry |
| `GET` | `/vendors/{id}/scorecard/` | Performance scorecard |
| `GET/POST` | `/rfqs/` | Create and manage RFQs |
| `POST` | `/rfqs/{id}/send/` | Send RFQ to vendors |
| `GET` | `/rfqs/{id}/quotes/` | Vendor quotes + AI ranking |
| `POST` | `/rfqs/{id}/award/` | Award to winning vendor |
| `GET` | `/contracts/` | All vendor contracts |
| `GET` | `/contracts/expiring/` | Contracts expiring in 60 days |
| `GET` | `/spend/analytics/` | Spend breakdown by vendor/category |
| `GET` | `/preferred-vendors/` | AI-recommended preferred vendors |

---

## Section 5: Tech Stack & Delivery

```
pip install reportlab django-apscheduler requests pdfplumber
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Vendor registry, RFQ creation and send, quote collection | Weeks 1–5 |
| Phase 2 | AI bid scoring, contract management, renewal alerts | Weeks 6–10 |
| Phase 3 | Approval workflow, spend analytics, performance scoring | Weeks 11–16 |

| Tier | Monthly | Vendors | Features |
|---|---|---|---|
| Intern | Free | 10 | Vendor registry + RFQ |
| Entry | ৳2,000 | 50 | Bid comparison, contract alerts |
| Mid | ৳5,000 | 200 | Approval workflow, performance scores |
| Senior | ৳10,000 | Unlimited | Spend analytics, preferred vendor AI |

*BengalBound HUB — dev branch*
