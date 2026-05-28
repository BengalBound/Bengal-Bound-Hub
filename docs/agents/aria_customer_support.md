# Module Requirements: Aria — AI Customer Support Specialist
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `aria_support` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Zendesk API, Intercom, Email SMTP, Slack, WhatsApp Business API

---

## Section 1: Overview

**AI Employee Name:** Aria Support | **Department:** Customer Support & Success
**Core Function:** Automates customer helpdesk responses, classifies inbound tickets, drafts instant contextual answers from the FAQ database, and handles escalation toggles to human team members when confidence is low.
**Value Prop:** *"Instant customer resolutions 24/7. Your support queue handled effortlessly."*

| | Human Support Agent | Aria Support AI |
|---|---|---|
| Monthly Cost | ৳18,000–৳30,000 | ৳2,000 |
| Response Speed | 15 minutes to 2 hours | Less than 10 seconds |
| Availability | Shift-based | 24/7/365 |
| Queue Escalation | Manual | Automatic confidence-based |

---

## Section 2: Core Capabilities

1. **Ticket Inbound Integration** — Connects directly to ZenDesk, Intercom, or inbound support mailboxes.
2. **AI Ticket Classification** — Automatically classifies tickets by department, urgency, and category (billing, technical, feedback, sales).
3. **Draft Auto-Resolution** — Automatically generates draft responses based on verified knowledge bases and FAQs.
4. **Confidence-based Escalation** — If AI confidence falls below 0.70, drafts the reply but routes it to the "Escalated" human queue instead of sending.
5. **Interactive FAQ Tuner** — Dashboard panel allowing business owners to easily update question-and-answer pairs.
6. **Support Metrics Dashboard** — Displays auto-resolution rates, average response time, and ticket volume distributions.
7. **Cross-Agent Coordination** — Passes double-billing or refund tickets directly to the Payroll / Finance agent (Cash).

---

## Section 3: Django Models

```python
from django.db import models

class AriaSupportConfig(models.Model):
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='ariasupport_configs')
    zendesk_url      = models.URLField(blank=True)
    zendesk_token    = models.TextField(blank=True)       # Encrypted
    escalation_email = models.EmailField(help_text="Standard mailbox for escalated tickets")
    auto_reply       = models.BooleanField(default=True)
    is_active        = models.BooleanField(default=True)

class SupportTicket(models.Model):
    STATUS_CHOICES = [('open','Open'),('escalated','Escalated'),('resolved','Resolved')]
    PRIORITY_CHOICES = [('low','Low'),('medium','Medium'),('high','High'),('urgent','Urgent')]
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='ariasupport_tickets')
    ticket_id        = models.CharField(max_length=100, unique=True)
    customer_email   = models.EmailField()
    subject          = models.CharField(max_length=255)
    description      = models.TextField()
    category         = models.CharField(max_length=100, blank=True)
    priority         = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    ai_draft_body    = models.TextField(blank=True)
    confidence_score = models.FloatField(default=1.0)
    created_at       = models.DateTimeField(auto_now_add=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/aria-support/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/config/` | View or configure ZenDesk settings and auto-reply switches |
| `GET` | `/tickets/` | List all tickets inside the support queue |
| `GET` | `/tickets/escalated/` | View tickets escalated to the human queue |
| `POST` | `/tickets/{id}/approve/` | Approve and send Serea's auto-draft response |
| `POST` | `/tickets/{id}/escalate/` | Manually mark a ticket as escalated |
| `POST` | `/webhooks/inbound-ticket/` | Receive inbound ticket callbacks, analyze, and draft reply |
| `GET` | `/analytics/` | SLA times, auto-resolution rates, ticket categories |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| Helpdesk API | Zendesk REST API (or Intercom REST API) | ✅ FREE |
| Inbound Email | IMAP / SMTP Client | ✅ FREE |
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
| Phase 1 | Tickets database CRUD, IMAP/SMTP inbound parsing, basic draft generation | Weeks 1–6 |
| Phase 2 | Zendesk API sync, confidence-based triage rules, automated escalation toggles | Weeks 7–12 |
| Phase 3 | Multi-channel messaging (WhatsApp/Intercom), advanced SLA timers, cross-agent coordination | Weeks 13–18 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | Tickets/mo | Features |
|---|---|---|---|
| Intern | Free | 50 | Inbound email ticketing, basic drafts |
| Entry | ৳2,000 | 250 | Confidence threshold filters, ticket category tagging |
| Mid | ৳5,000 | 1000 | Zendesk integration, SLA metrics tracker, manual tuner |
| Senior | ৳10,000 | Unlimited | Multi-channel chat integrations, cross-agent routing, full analytics |

---
*BengalBound HUB — dev branch*
