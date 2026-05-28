# Module Requirements: Crux — AI CRM Manager
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `crux` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 HubSpot API, Pipedrive API, Salesforce API, Gmail, WhatsApp

---

## Section 1: Overview

**AI Employee Name:** Crux | **Department:** Sales Operations
**Core Function:** Keeps the CRM clean and current — logs every interaction, updates contact records, segments leads by intent score, and triggers perfectly-timed follow-up sequences automatically.
**Value Prop:** *"Your CRM updates itself. Your pipeline never goes cold."*

| | Human CRM Admin | Crux AI |
|---|---|---|
| Monthly Cost | ৳20,000–৳35,000 | ৳2,000 |
| Data Entry | Manual, error-prone | Automatic, real-time |
| Follow-up Timing | Guesswork | AI-optimized |
| Lead Segmentation | Periodic batch | Continuous scoring |

---

## Section 2: Core Capabilities

1. **Auto-Log Interactions** — Every email, call, meeting, and WhatsApp message automatically logged to CRM contact record
2. **Contact Enrichment** — Pulls company data, LinkedIn profile, and recent news for every contact
3. **Intent Segmentation** — AI scores contacts 0–100 for purchase intent; auto-moves between pipeline stages
4. **Follow-Up Sequences** — Triggers personalized email/WhatsApp follow-up at optimal time based on contact behavior
5. **Deal Health Monitor** — Flags deals with no activity for 7+ days as "Going Cold" with recommended next action
6. **Pipeline Analytics** — Daily snapshot of pipeline value, win rate, avg deal cycle, and conversion by stage
7. **Duplicate Detector** — Identifies and merges duplicate contact/company records

---

## Section 3: Django Models

```python
class CRMIntegration(models.Model):
    PLATFORMS = [('hubspot','HubSpot'),('pipedrive','Pipedrive'),('salesforce','Salesforce')]
    business     = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='crux_crmintegrations')
    platform     = models.CharField(max_length=20, choices=PLATFORMS)
    api_key      = models.TextField()          # Encrypted
    portal_id    = models.CharField(max_length=100, blank=True)
    is_active    = models.BooleanField(default=True)

class Contact(models.Model):
    business     = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='crux_contacts')
    crm_id       = models.CharField(max_length=200)
    name         = models.CharField(max_length=300)
    email        = models.EmailField(blank=True)
    phone        = models.CharField(max_length=50, blank=True)
    company      = models.CharField(max_length=300, blank=True)
    intent_score = models.IntegerField(null=True)       # 0–100 AI score
    pipeline_stage = models.CharField(max_length=100, blank=True)
    last_activity  = models.DateTimeField(null=True)
    days_inactive  = models.IntegerField(default=0)
    is_cold        = models.BooleanField(default=False)
    enriched_data  = models.JSONField(default=dict)
    last_synced    = models.DateTimeField(null=True)

class Interaction(models.Model):
    TYPES = [('email','Email'),('call','Call'),('meeting','Meeting'),
             ('whatsapp','WhatsApp'),('note','Note')]
    contact      = models.ForeignKey(Contact, on_delete=models.CASCADE)
    type         = models.CharField(max_length=20, choices=TYPES)
    summary      = models.TextField()          # Gemini-generated summary
    sentiment    = models.CharField(max_length=20, blank=True)  # 'positive','neutral','negative'
    crm_logged   = models.BooleanField(default=False)
    occurred_at  = models.DateTimeField()
    logged_at    = models.DateTimeField(auto_now_add=True)

class FollowUpSequence(models.Model):
    STATUS = [('scheduled','Scheduled'),('sent','Sent'),('replied','Replied'),('skipped','Skipped')]
    contact      = models.ForeignKey(Contact, on_delete=models.CASCADE)
    channel      = models.CharField(max_length=20)
    message_body = models.TextField()
    send_at      = models.DateTimeField()
    status       = models.CharField(max_length=20, choices=STATUS, default='scheduled')
    sent_at      = models.DateTimeField(null=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/crux/`)

| Method | Endpoint | Action |
|---|---|---|
| `POST` | `/integrations/connect/` | Connect HubSpot/Pipedrive/Salesforce |
| `GET` | `/contacts/` | List contacts with intent scores |
| `GET` | `/contacts/cold/` | Deals going cold (7+ days inactive) |
| `POST` | `/contacts/{id}/log-interaction/` | Manual interaction log |
| `GET` | `/contacts/{id}/follow-ups/` | Upcoming follow-up sequences |
| `POST` | `/contacts/{id}/trigger-sequence/` | Start a follow-up sequence |
| `GET` | `/pipeline/` | Pipeline health snapshot |
| `GET` | `/analytics/` | Win rate, conversion, deal velocity |
| `POST` | `/duplicates/detect/` | Scan for duplicate contacts |
| `POST` | `/duplicates/merge/` | Merge duplicate records |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash | ✅ FREE |
| HubSpot | `hubspot-api-client` | ✅ FREE |
| Pipedrive | Pipedrive REST API | ✅ FREE |
| Enrichment | Apollo.io API | 💲 $49/mo |
| Task Queue | `django-apscheduler` | ✅ FREE |
| Email | Gmail SMTP | ✅ FREE |

```
pip install hubspot-api-client requests django-apscheduler
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | HubSpot connect, interaction logging, intent scoring, cold deal alerts | Weeks 1–6 |
| Phase 2 | Follow-up sequences, Pipedrive, duplicate detection, pipeline analytics | Weeks 7–12 |
| Phase 3 | Salesforce, contact enrichment (Apollo), WhatsApp logging, AI next-action suggestions | Weeks 13–18 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | Contacts | Features |
|---|---|---|---|
| Intern | Free | 100 | Sync + intent scoring |
| Entry | ৳2,000 | 500 | Follow-up sequences, cold alerts |
| Mid | ৳5,000 | 2,000 | Enrichment, duplicate detection, analytics |
| Senior | ৳10,000 | Unlimited | All CRMs, WhatsApp, AI suggestions |

---
*BengalBound HUB — dev branch*
