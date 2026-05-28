# Module Requirements: Realt — AI Real Estate Assistant
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `realt` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 WhatsApp Business API, Google Calendar, Facebook Marketplace API, bdjobs/property portal webhooks

---

## Section 1: Overview

**AI Employee Name:** Realt | **Department:** Real Estate
**Target Clients:** Real estate agencies, property developers, independent agents, and property management companies in Bangladesh and abroad.
**Core Function:** Qualifies buyer/tenant inquiries, schedules property viewings, sends listing updates, drafts offer summaries, and keeps the agent focused on closing — not admin.
**Value Prop:** *"Every lead qualified. Every viewing booked. Agents close deals, not calendars."*

| | Human Property Agent | Realt AI |
|---|---|---|
| Monthly Cost | ৳20,000–৳35,000 | ৳2,000 |
| Lead Response | Hours (business hours) | Seconds (24/7) |
| Listing Updates | Manual | Automated |
| Viewing Scheduling | Phone/email back-and-forth | Instant self-service |

---

## Section 2: Core Capabilities

1. **Lead Qualification Bot** — WhatsApp/web chat bot qualifies inbound inquiries (budget, location, size, timeline, buy/rent)
2. **Listing Management** — AI writes and updates property listings with compelling descriptions; posts to portals
3. **Viewing Scheduler** — Qualified leads self-book viewings into agent's Google Calendar via automated flow
4. **Listing Alert System** — Matched buyers/tenants automatically notified when a new property matching their criteria lists
5. **Offer Summary Drafting** — Gemini drafts formal offer summaries and sends to both parties for review
6. **Property Market Report** — Monthly AI-generated neighborhood market report (avg price/sqft, demand trends)
7. **Document Checklist** — Auto-sends document checklist to buyer/tenant after offer accepted (NID, bank statement, etc.)

---

## Section 3: Django Models

```python
class AgencyProfile(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='realt_agencyprofiles')
    agency_name     = models.CharField(max_length(300))
    license_no      = models.CharField(max_length(100), blank=True)
    service_areas   = models.JSONField(default=list)     # ['Gulshan', 'Dhanmondi', 'Uttara']
    specialties     = models.JSONField(default=list)     # ['residential', 'commercial', 'rental']

class Property(models.Model):
    STATUS = [('available','Available'),('viewing','Viewing Scheduled'),
              ('under_offer','Under Offer'),('sold','Sold'),('rented','Rented')]
    TYPES = [('apartment','Apartment'),('house','House'),('commercial','Commercial'),
             ('land','Land'),('office','Office')]
    agency          = models.ForeignKey(AgencyProfile, on_delete=models.CASCADE)
    title           = models.CharField(max_length(500))
    property_type   = models.CharField(max_length(20), choices=TYPES)
    listing_type    = models.CharField(max_length(10))   # 'sale' or 'rent'
    price           = models.DecimalField(max_digits=14, decimal_places=2)
    area_sqft       = models.IntegerField()
    bedrooms        = models.IntegerField(null=True)
    location        = models.CharField(max_length(300))
    description     = models.TextField()                 # AI-generated
    images          = models.JSONField(default=list)     # Image URLs
    status          = models.CharField(max_length(20), choices=STATUS, default='available')
    listed_at       = models.DateTimeField(auto_now_add=True)

class Lead(models.Model):
    STATUS = [('new','New'),('qualified','Qualified'),('viewing_booked','Viewing Booked'),
              ('offer_made','Offer Made'),('converted','Converted'),('rejected','Rejected')]
    agency          = models.ForeignKey(AgencyProfile, on_delete=models.CASCADE)
    name            = models.CharField(max_length(300))
    phone           = models.CharField(max_length(30))
    email           = models.EmailField(blank=True)
    intent          = models.CharField(max_length(10))   # 'buy' or 'rent'
    budget_min      = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    budget_max      = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    preferred_areas = models.JSONField(default=list)
    bedrooms_needed = models.IntegerField(null=True)
    timeline        = models.CharField(max_length(100), blank=True)  # 'immediately', '3 months'
    ai_score        = models.IntegerField(null=True)                 # 0–100 qualification score
    status          = models.CharField(max_length(20), choices=STATUS, default='new')
    source          = models.CharField(max_length(50), blank=True)   # 'whatsapp', 'web', 'portal'
    created_at      = models.DateTimeField(auto_now_add=True)

class Viewing(models.Model):
    lead            = models.ForeignKey(Lead, on_delete=models.CASCADE)
    property        = models.ForeignKey(Property, on_delete=models.CASCADE)
    scheduled_at    = models.DateTimeField()
    agent           = models.CharField(max_length(200))
    calendar_event  = models.CharField(max_length(200), blank=True)
    attended        = models.BooleanField(null=True)
    feedback        = models.TextField(blank=True)
    offer_made      = models.BooleanField(default=False)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/realt/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/properties/` | Manage property listings |
| `POST` | `/properties/{id}/generate-description/` | AI-generate listing description |
| `GET` | `/leads/` | List leads with qualification scores |
| `GET` | `/leads/qualified/` | Fully qualified leads only |
| `POST` | `/leads/{id}/book-viewing/` | Schedule property viewing |
| `POST` | `/leads/{id}/send-matches/` | Send matching property listings |
| `GET` | `/viewings/` | Upcoming viewings schedule |
| `POST` | `/viewings/{id}/feedback/` | Log post-viewing feedback |
| `POST` | `/properties/{id}/generate-offer/` | Draft offer summary document |
| `GET` | `/analytics/` | Leads, viewings, conversion rate, avg days-to-close |
| `GET` | `/market-report/{area}/` | AI neighborhood market report |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash | ✅ FREE |
| WhatsApp Bot | WhatsApp Business API | 💲 Per conversation |
| Calendar | Google Calendar API | ✅ FREE |
| PDF Offers | `reportlab` | ✅ FREE |
| Email | Gmail SMTP | ✅ FREE |
| Task Queue | `django-apscheduler` | ✅ FREE |

```
pip install reportlab google-api-python-client google-auth django-apscheduler
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Lead qualification form, property listings, viewing scheduler, Google Calendar sync | Weeks 1–6 |
| Phase 2 | WhatsApp qualification bot, listing alert system, offer draft generator | Weeks 7–12 |
| Phase 3 | Market report, portal integration (Bproperty/Lamudi), document checklist, analytics | Weeks 13–18 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | Listings | Features |
|---|---|---|---|
| Intern | Free | 5 | Lead form, dashboard |
| Entry | ৳2,000 | 20 | Viewing scheduler, listing alerts |
| Mid | ৳5,000 | 100 | WhatsApp bot, offer drafts, analytics |
| Senior | ৳10,000 | Unlimited | Market reports, portal sync, multi-agent |

---
*BengalBound HUB — dev branch*
