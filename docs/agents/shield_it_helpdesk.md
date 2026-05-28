# Module Requirements: Shield — AI IT Helpdesk Support
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `shield_helpdesk` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Jira Service Desk, Freshdesk, Slack, Microsoft Teams, email

---

## Section 1: Overview

**AI Employee Name:** Shield | **Department:** IT Support
**Core Function:** Handles Tier-1 IT support tickets automatically — password resets, software install guidance, connectivity troubleshooting, and access requests — escalating only what it can't resolve to a human engineer.
**Value Prop:** *"80% of IT tickets resolved in under 2 minutes. No helpdesk queue. No waiting."*

| | Human IT Helpdesk | Shield AI |
|---|---|---|
| Monthly Cost | ৳20,000–৳35,000 | ৳2,000 |
| Response Time | 30–120 minutes | Under 2 minutes |
| Tier-1 Resolution | ~60% | ~80% |
| Availability | Business hours | 24/7 |

---

## Section 2: Core Capabilities

1. **Ticket Triage** — Every support request classified by: category (hardware/software/network/access), urgency, and estimated resolution complexity
2. **Tier-1 Auto-Resolution** — Gemini provides step-by-step troubleshooting for: password resets, VPN issues, software installation, email config, printer setup, common error codes
3. **Knowledge Base Building** — Every successfully resolved ticket adds a solution to the searchable knowledge base
4. **Access Request Workflow** — Employees request system access → Shield verifies role authorization → routes to IT admin for approval → notifies employee on completion
5. **Escalation Routing** — Tier-2/3 issues routed to correct engineer with full ticket context and Shield's attempted solutions
6. **SLA Monitoring** — Tracks resolution time against SLA; alerts if tickets are approaching breach
7. **IT Asset Tracker** — Logs all company devices, software licenses, and expiry dates
8. **Weekly IT Health Report** — Ticket volume, resolution rate, top issues, SLA compliance, open backlog

---

## Section 3: Django Models

```python
class Ticket(models.Model):
    CATEGORIES = [('hardware','Hardware'),('software','Software'),('network','Network'),
                  ('access','Access Request'),('email','Email'),('other','Other')]
    PRIORITY = [('low','Low'),('medium','Medium'),('high','High'),('critical','Critical')]
    STATUS = [('open','Open'),('ai_resolving','AI Resolving'),('waiting_user','Waiting on User'),
              ('escalated','Escalated'),('resolved','Resolved'),('closed','Closed')]
    TIERS = [('t1','Tier 1 — AI'),('t2','Tier 2 — Engineer'),('t3','Tier 3 — Senior')]

    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='shield_helpdesk_tickets')
    submitted_by     = models.CharField(max_length=300)
    submitted_via    = models.CharField(max_length=30)  # 'email','slack','web','teams'
    title            = models.CharField(max_length(500))
    description      = models.TextField()
    category         = models.CharField(max_length=20, choices=CATEGORIES)
    priority         = models.CharField(max_length=10, choices=PRIORITY)
    status           = models.CharField(max_length=20, choices=STATUS, default='open')
    tier             = models.CharField(max_length=5, choices=TIERS, default='t1')
    ai_solution      = models.TextField(blank=True)
    ai_confidence    = models.FloatField(null=True)
    assigned_to      = models.CharField(max_length=200, blank=True)
    sla_hours        = models.IntegerField(default=4)
    sla_breached     = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)
    resolved_at      = models.DateTimeField(null=True)

class KnowledgeArticle(models.Model):
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='shield_helpdesk_knowledgearticles')
    title            = models.CharField(max_length=500)
    category         = models.CharField(max_length=20)
    problem          = models.TextField()
    solution         = models.TextField()
    success_count    = models.IntegerField(default=1)
    source_ticket    = models.ForeignKey(Ticket, on_delete=models.SET_NULL, null=True)
    created_at       = models.DateTimeField(auto_now_add=True)

class ITAsset(models.Model):
    TYPES = [('laptop','Laptop'),('desktop','Desktop'),('phone','Phone'),
             ('license','Software License'),('server','Server'),('peripheral','Peripheral')]
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='shield_helpdesk_itassets')
    name             = models.CharField(max_length=300)
    asset_type       = models.CharField(max_length=20, choices=TYPES)
    serial_number    = models.CharField(max_length=200, blank=True)
    assigned_to      = models.CharField(max_length=300, blank=True)
    purchase_date    = models.DateField(null=True)
    warranty_expiry  = models.DateField(null=True)
    license_expiry   = models.DateField(null=True)
    is_active        = models.BooleanField(default=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/shield/`)

| Method | Endpoint | Action |
|---|---|---|
| `POST` | `/tickets/` | Submit new ticket |
| `GET` | `/tickets/` | List all tickets |
| `GET` | `/tickets/{id}/` | Ticket detail + AI solution |
| `POST` | `/tickets/{id}/escalate/` | Escalate to human engineer |
| `POST` | `/tickets/{id}/resolve/` | Mark as resolved |
| `GET` | `/tickets/sla-at-risk/` | Tickets approaching SLA breach |
| `GET` | `/knowledge-base/` | Search knowledge articles |
| `GET/POST` | `/assets/` | Manage IT assets |
| `GET` | `/assets/expiring/` | Licenses/warranties expiring in 30 days |
| `GET` | `/analytics/` | Resolution rate, avg time, SLA compliance, top categories |

---

## Section 5: Tech Stack & Delivery

**Key Packages:** `django-apscheduler requests`

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Ticket submission, AI triage, Tier-1 resolution, email channel | Weeks 1–5 |
| Phase 2 | Slack/Teams integration, knowledge base builder, SLA monitoring, escalation | Weeks 6–10 |
| Phase 3 | IT asset tracker, access request workflow, weekly IT report, Jira/Freshdesk sync | Weeks 11–16 |

| Tier | Monthly | Tickets/mo | Features |
|---|---|---|---|
| Intern | Free | 50 | AI resolution + basic dashboard |
| Entry | ৳2,000 | 200 | SLA tracking, knowledge base |
| Mid | ৳5,000 | 1,000 | Slack/Teams, asset tracker, escalation |
| Senior | ৳10,000 | Unlimited | Jira sync, access workflows, reports |

*BengalBound HUB — dev branch*
