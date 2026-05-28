# Module Requirements: Mira — AI Customer Success Manager
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `mira` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 HubSpot, Intercom, Zendesk, Stripe, NPS tools, email

---

## Section 1: Overview

**AI Employee Name:** Mira | **Department:** Customer Success
**Core Function:** Monitors client health scores, predicts churn 30 days in advance, automates onboarding sequences, sends check-in emails, and escalates at-risk accounts to human CSMs before they cancel.
**Value Prop:** *"Churn caught before it happens. Every client feels looked after, automatically."*

| | Human CSM | Mira AI |
|---|---|---|
| Monthly Cost | ৳30,000–৳50,000 | ৳2,000 |
| Clients Managed | 20–40 | Unlimited |
| Churn Detection | Reactive | 30 days predictive |
| Onboarding | Manual | Automated sequences |

---

## Section 2: Core Capabilities

1. **Health Score Monitoring** — Scores each client 0–100 based on: login frequency, feature usage, support tickets, NPS, payment history
2. **Churn Prediction** — Gemini identifies at-risk clients 30 days before likely churn; triggers intervention workflow
3. **Automated Onboarding** — Day 1/3/7/14/30 email sequence with setup tips, feature spotlights, and video guides
4. **Proactive Check-Ins** — Monthly AI-drafted check-in emails personalised to the client's usage patterns
5. **NPS Collection & Analysis** — Sends quarterly NPS surveys; Gemini analyses open-text responses for themes
6. **Upsell Detection** — Identifies clients approaching tier limits or using features heavily — flags for upsell conversation
7. **Renewal Alerts** — 90/60/30 day renewal reminders with account summary for human review
8. **Escalation Routing** — If health score drops below 40, creates urgent task for human CSM with full context brief

---

## Section 3: Django Models

```python
class ClientHealth(models.Model):
    RISK = [('healthy','Healthy'),('at_risk','At Risk'),('critical','Critical'),('churned','Churned')]
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='mira_clienthealths')
    health_score     = models.IntegerField()         # 0–100
    risk_level       = models.CharField(max_length=10, choices=RISK)
    login_frequency  = models.FloatField()           # Avg logins/week
    feature_usage    = models.FloatField()           # % of features used
    open_tickets     = models.IntegerField(default=0)
    last_nps_score   = models.IntegerField(null=True)
    payment_overdue  = models.BooleanField(default=False)
    days_since_login = models.IntegerField(default=0)
    churn_probability = models.FloatField(null=True) # 0.0–1.0 (Gemini prediction)
    ai_summary       = models.TextField(blank=True)  # What's driving the health score
    checked_at       = models.DateTimeField(auto_now=True)

class OnboardingSequence(models.Model):
    STATUS = [('active','Active'),('completed','Completed'),('paused','Paused')]
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='mira_onboardingsequences')
    current_step     = models.IntegerField(default=1)  # Day 1/3/7/14/30
    status           = models.CharField(max_length=20, choices=STATUS, default='active')
    started_at       = models.DateTimeField(auto_now_add=True)
    completed_at     = models.DateTimeField(null=True)

class SuccessEmail(models.Model):
    TYPES = [('onboarding','Onboarding'),('checkin','Check-In'),
             ('nps','NPS Survey'),('renewal','Renewal'),('upsell','Upsell'),('intervention','Intervention')]
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='mira_successemails')
    email_type       = models.CharField(max_length=20, choices=TYPES)
    subject          = models.CharField(max_length=500)
    body             = models.TextField()
    sent             = models.BooleanField(default=False)
    sent_at          = models.DateTimeField(null=True)
    opened           = models.BooleanField(default=False)
    replied          = models.BooleanField(default=False)
    generated_at     = models.DateTimeField(auto_now_add=True)

class NPSResponse(models.Model):
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='mira_npsresponses')
    score            = models.IntegerField()          # 0–10
    comment          = models.TextField(blank=True)
    sentiment        = models.CharField(max_length=20, blank=True)
    themes           = models.JSONField(default=list) # Gemini-extracted themes
    responded_at     = models.DateTimeField(auto_now_add=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/mira/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET` | `/health/` | All client health scores |
| `GET` | `/health/at-risk/` | At-risk and critical clients |
| `POST` | `/health/{id}/refresh/` | Recalculate health score |
| `GET` | `/onboarding/{client_id}/` | Onboarding progress |
| `GET` | `/emails/` | Sent emails + open/reply tracking |
| `POST` | `/emails/send-checkin/` | Trigger check-in email now |
| `GET` | `/nps/` | All NPS responses + themes |
| `POST` | `/nps/send-survey/` | Send NPS survey to a client |
| `GET` | `/upsell-candidates/` | Clients flagged for upsell |
| `GET` | `/renewals/upcoming/` | Upcoming renewals |
| `GET` | `/analytics/` | Churn rate, avg health, NPS trend |

---

## Section 5: Tech Stack & Delivery

**Key Packages:** `django-apscheduler requests`

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Health scoring, onboarding sequence, churn alert, check-in emails | Weeks 1–6 |
| Phase 2 | NPS survey + analysis, upsell detection, renewal alerts, escalation | Weeks 7–12 |
| Phase 3 | HubSpot/Intercom sync, Stripe usage data, predictive churn model | Weeks 13–18 |

| Tier | Monthly | Clients | Features |
|---|---|---|---|
| Intern | Free | 10 | Health score, dashboard |
| Entry | ৳2,000 | 50 | Onboarding, check-ins, churn alerts |
| Mid | ৳5,000 | 200 | NPS, upsell detection, renewal mgmt |
| Senior | ৳10,000 | Unlimited | CRM sync, predictive churn, analytics |

*BengalBound HUB — dev branch*
