# Module Requirements: Concierge — AI Client Concierge
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `concierge` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 WhatsApp Business API, Google Calendar, HubSpot, web chat widget

---

## Section 1: Overview

**AI Employee Name:** Concierge | **Department:** Sales & Customer Support
**Target Clients:** Service businesses, agencies, consultants, SaaS companies — any business with inbound leads that need qualifying and nurturing before a sales call.
**Core Function:** A 24/7 WhatsApp and web chat agent that greets every inbound lead, qualifies them against the ICP, answers FAQs from a knowledge base, and books discovery calls directly into the CEO/sales team's calendar — zero manual follow-up required.
**Value Prop:** *"Every lead welcomed. Every question answered. Every call booked. While you sleep."*

| | Human Sales Rep | Concierge AI |
|---|---|---|
| Monthly Cost | ৳12,000–৳20,000 | ৳2,000 |
| Response Time | Business hours | Seconds, 24/7 |
| Lead Qualification | Inconsistent | Structured AI scoring |
| Meeting Booking | Manual scheduling | Instant calendar sync |

---

## Section 2: Core Capabilities

1. **WhatsApp Lead Greeting** — Every new WhatsApp inquiry receives an instant branded greeting and qualification sequence
2. **Web Chat Widget** — Embeddable JavaScript widget for the client's website; same AI engine as WhatsApp
3. **Lead Qualification Flow** — Conversational AI asks: what do you need, company size, timeline, budget range — scores intent 0–100
4. **FAQ Answering** — Answers from a client-built knowledge base (pricing, services, process, turnaround)
5. **Discovery Call Booking** — Qualified leads select a meeting slot directly in the conversation; syncs with Google Calendar or Calendly
6. **Handoff Summary** — Before every booked call, sends the sales team a lead brief: company, pain point, budget, qualification score
7. **Nurture Sequences** — Unqualified or not-ready leads entered into automated nurture (weekly valuable content for 4 weeks)

---

## Section 3: Django Models

```python
class ConciergeConfig(models.Model):
    business            = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='concierge_conciergeconfigs')
    brand_name          = models.CharField(max_length(200))
    greeting_message    = models.TextField()
    calendar_link       = models.URLField(blank=True)         # Calendly or Google Cal link
    whatsapp_number     = models.CharField(max_length(30), blank=True)
    min_budget          = models.IntegerField(null=True)      # Minimum qualified budget
    target_company_size = models.JSONField(default=list)      # ['1-10', '11-50']
    qualification_threshold = models.IntegerField(default=65) # Min score to book call

class KnowledgeBaseEntry(models.Model):
    business    = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='concierge_knowledgebaseentries')
    question    = models.TextField()
    answer      = models.TextField()
    category    = models.CharField(max_length(100), blank=True)  # 'pricing', 'process', 'services'
    is_active   = models.BooleanField(default=True)

class Conversation(models.Model):
    CHANNELS = [('whatsapp','WhatsApp'),('web_chat','Web Chat'),('instagram','Instagram DM')]
    STATUS = [('active','Active'),('qualified','Qualified'),('unqualified','Unqualified'),
              ('booked','Meeting Booked'),('nurturing','In Nurture'),('closed','Closed')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='concierge_conversations')
    channel         = models.CharField(max_length(20), choices=CHANNELS)
    lead_name       = models.CharField(max_length(300), blank=True)
    lead_contact    = models.CharField(max_length(200))   # Phone or email
    lead_company    = models.CharField(max_length(300), blank=True)
    pain_point      = models.TextField(blank=True)
    budget_stated   = models.CharField(max_length(100), blank=True)
    timeline        = models.CharField(max_length(100), blank=True)
    qualification_score = models.IntegerField(null=True)
    status          = models.CharField(max_length(20), choices=STATUS, default='active')
    meeting_booked_at   = models.DateTimeField(null=True)
    calendar_event  = models.CharField(max_length(200), blank=True)
    started_at      = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True)

class Message(models.Model):
    SENDERS = [('lead','Lead'),('ai','AI Concierge'),('human','Human Agent')]
    conversation    = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    sender          = models.CharField(max_length(20), choices=SENDERS)
    text            = models.TextField()
    sent_at         = models.DateTimeField(auto_now_add=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/concierge/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/config/` | Manage concierge configuration |
| `GET/POST` | `/knowledge-base/` | Manage FAQ knowledge base |
| `POST` | `/webhook/whatsapp/` | WhatsApp message webhook |
| `POST` | `/widget/message/` | Web chat widget message handler |
| `GET` | `/conversations/` | List all conversations |
| `GET` | `/conversations/qualified/` | Qualified leads ready for follow-up |
| `GET` | `/conversations/{id}/` | Conversation transcript |
| `POST` | `/conversations/{id}/handoff/` | Escalate to human agent |
| `POST` | `/conversations/{id}/enter-nurture/` | Place lead in nurture sequence |
| `GET` | `/analytics/` | Lead volume, qualification rate, booking rate, response time |
| `GET` | `/meetings/upcoming/` | Upcoming booked discovery calls |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash | ✅ FREE |
| WhatsApp | WhatsApp Business API (Meta) | 💲 Per conversation |
| Calendar | Google Calendar API / Calendly webhook | ✅ FREE |
| Web Widget | Vanilla JS embeddable widget | ✅ FREE |
| Task Queue | `django-apscheduler` | ✅ FREE |
| Email | Gmail SMTP | ✅ FREE |

```
pip install google-api-python-client google-auth django-apscheduler requests
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Web chat widget, Gemini qualification flow, knowledge base, Calendly booking, handoff brief | Weeks 1–6 |
| Phase 2 | WhatsApp integration, nurture sequences, HubSpot lead push, conversation analytics | Weeks 7–12 |
| Phase 3 | Instagram DM, multi-agent escalation, A/B qualification scripts, revenue attribution | Weeks 13–18 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | Conversations/mo | Features |
|---|---|---|---|
| Intern | Free | 30 | Web chat, basic FAQ |
| Entry | ৳2,000 | 200 | WhatsApp, calendar booking, handoff brief |
| Mid | ৳5,000 | 1,000 | Nurture sequences, HubSpot, analytics |
| Senior | ৳10,000 | Unlimited | Multi-channel, A/B scripts, revenue tracking |

---
*BengalBound HUB — dev branch*
