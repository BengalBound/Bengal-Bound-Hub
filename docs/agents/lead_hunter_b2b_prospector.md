# Module Requirements: Lead Hunter — AI B2B Prospector
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `lead_hunter` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Apollo.io, Gmail, Outlook SMTP, Hubspot, Twilio SMS

---

## Section 1: Overview

**AI Employee Name:** Lead Hunter | **Department:** Sales & Business Development
**Core Function:** Automates B2B cold email outreach sequences, prospect list building, sentiment-based reply triage, and triggers real-time Hubspot syncs when a buyer expresses interest.
**Value Prop:** *"Outbound pipeline running on autopilot. Constant flow of highly-qualified sales opportunities."*

| | Human SDR / BDR | Lead Hunter AI |
|---|---|---|
| Monthly Cost | ৳25,000–৳45,000 | ৳2,000 |
| Daily Prospecting Capacity | 20–50 prospects | 500+ prospects |
| Personalisation Level | Semi-templated | AI hyper-personalised |
| Sequence Triage | Manual inbox review | AI-triage within 5 minutes |

---

## Section 2: Core Capabilities

1. **Lead Search Integration** — Query-based search inside Apollo.io to harvest targeted contacts.
2. **Cold Outreach Sequencing** — Dynamically schedules multiple follow-up stages (Day 1 Intro -> Day 3 Value Prop -> Day 7 Follow-up).
3. **Hyper-Personalised Templates** — Gemini inserts custom context from Apollo datasets (company size, recent achievements, tech stack) for every email.
4. **Reply Triage & Sentiment Analysis** — Auto-reads reply emails, categorizing them as "Interested", "Not Interested", "Ask Later", or "Out of Office".
5. **Human Escalation Alert** — Alerts a human salesperson via email or Slack the moment a prospect replies with purchase intent.
6. **Outbox Synchronization** — Connects to the user's custom SMTP (Gmail/Outlook) to send outbound emails directly from their address.
7. **Hubspot Sync** — Auto-creates leads or deals in CRM upon intent confirmation.

---

## Section 3: Django Models

```python
from django.db import models

class LeadHunterConfig(models.Model):
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='leadhunter_configs')
    apollo_api_key   = models.CharField(max_length=255, blank=True)
    sender_email     = models.EmailField()
    smtp_host        = models.CharField(max_length=100)
    smtp_port        = models.IntegerField(default=587)
    smtp_username    = models.CharField(max_length=100)
    smtp_password    = models.TextField()               # Encrypted
    is_active        = models.BooleanField(default=True)

class OutreachCampaign(models.Model):
    STATUS_CHOICES = [('draft','Draft'),('active','Active'),('paused','Paused'),('completed','Completed')]
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='leadhunter_campaigns')
    name             = models.CharField(max_length=200)
    subject_template = models.CharField(max_length=300)
    body_stages      = models.JSONField(default=list, help_text="List of sequence bodies, e.g. ['Stage 1...', 'Stage 2...']")
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at       = models.DateTimeField(auto_now_add=True)

class Prospect(models.Model):
    STAGE_CHOICES = [('discovered','Discovered'),('contacted','Contacted'),('replied','Replied'),('unsubscribed','Unsubscribed')]
    INTENT_CHOICES = [('undecided','Undecided'),('interested','Interested'),('not_interested','Not Interested'),('out_of_office','Out of Office')]
    campaign         = models.ForeignKey(OutreachCampaign, on_delete=models.CASCADE, related_name='prospects')
    first_name       = models.CharField(max_length=100)
    last_name        = models.CharField(max_length=100)
    email            = models.EmailField()
    company_name     = models.CharField(max_length=200)
    job_title        = models.CharField(max_length=200)
    current_stage    = models.CharField(max_length=20, choices=STAGE_CHOICES, default='discovered')
    reply_intent     = models.CharField(max_length=20, choices=INTENT_CHOICES, default='undecided')
    custom_variables = models.JSONField(default=dict, help_text="Data gathered from Apollo: size, country, stack")
    last_contacted   = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/lead-hunter/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/config/` | Retrieve or set Apollo & SMTP configuration |
| `GET/POST` | `/campaigns/` | Create or list outreach campaigns |
| `POST` | `/campaigns/{id}/search/` | Connect with Apollo and discover prospects based on query |
| `GET` | `/prospects/` | List all discovered prospects |
| `GET` | `/prospects/interested/` | View hot leads who replied showing interest |
| `POST` | `/prospects/{id}/send-sequence/` | Trigger the next email sequence stage manually |
| `POST` | `/webhooks/email-reply/` | Receive inbound email callbacks, evaluate intent, and alerts CEO |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| Data & B2B Leads | Apollo.io REST API | 💲 $49/mo (or Free API tier) |
| Outbox System | SMTP Client (Gmail/Outlook) | ✅ FREE |
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash | ✅ FREE |
| Task Queue | Celery + Redis | ✅ FREE |

```
pip install requests django-encrypted-model-fields
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | SMTP connect, Apollo lead search, basic templates, prospect roster | Weeks 1–6 |
| Phase 2 | Automated sequencers, email templates variables injection, AI reply intent categorization | Weeks 7–12 |
| Phase 3 | Hubspot auto-deals creation, SMS outreach integration, advanced conversion analytics | Weeks 13–18 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | Daily Emails | Features |
|---|---|---|---|
| Intern | Free | 20 | Single template outreach, prospect roster |
| Entry | ৳2,000 | 100 | Full sequencers, basic personalized variables |
| Mid | ৳5,000 | 500 | AI intent categorization, Apollo integration, duplicate filters |
| Senior | ৳10,000 | Unlimited | Hubspot CRM auto-sync, SMS sequences, smart outbox warming |

---
*BengalBound HUB — dev branch*
