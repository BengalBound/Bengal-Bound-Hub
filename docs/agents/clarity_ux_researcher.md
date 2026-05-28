# Module Requirements: Clarity — AI UX Researcher & Customer Insight Analyst
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `clarity` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)

---

## Section 1: Overview

**AI Employee Name:** Clarity | **Department:** Product & UX
**Core Function:** Collects user feedback, analyses support tickets, conducts automated user interviews, synthesises insights into actionable product recommendations, and tracks feature sentiment over time.
**Value Prop:** *"Know exactly what your users want — before they churn to a competitor that figured it out first."*

---

## Section 2: Core Capabilities

1. **Feedback Collection** — In-app widgets, post-session surveys, and email surveys automatically distributed
2. **Support Ticket Mining** — Gemini analyses all support tickets to surface recurring pain points and feature requests
3. **Automated User Interviews** — AI conducts text-based interviews via email/WhatsApp; synthesises themes from open responses
4. **Sentiment Tracking** — Tracks product sentiment by feature, user segment, and time period
5. **Feature Request Prioritisation** — Ranks feature requests by frequency, user segment value, and strategic alignment
6. **Insight Report Generator** — Monthly research report: top user pain points, top requests, NPS drivers, churn risk signals
7. **Heatmap & Session Notes Integration** — Connects to Hotjar/FullStory for behavioural signals alongside qualitative feedback
8. **Persona Builder** — Gemini synthesises user interview data into 3–5 actionable user personas

---

## Section 3: Django Models

```python
class FeedbackSurvey(models.Model):
    TYPES = [('in_app','In-App Widget'),('post_session','Post Session'),
             ('nps','NPS'),('feature','Feature Feedback'),('exit','Exit Survey')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='clarity_feedbacksurveys')
    name            = models.CharField(max_length=300)
    survey_type     = models.CharField(max_length=20, choices=TYPES)
    questions       = models.JSONField(default=list)
    is_active       = models.BooleanField(default=True)
    responses_count = models.IntegerField(default=0)
    created_at      = models.DateTimeField(auto_now_add=True)

class FeedbackResponse(models.Model):
    survey          = models.ForeignKey(FeedbackSurvey, on_delete=models.CASCADE)
    respondent_id   = models.CharField(max_length=200, blank=True)
    answers         = models.JSONField()
    sentiment       = models.CharField(max_length=20, blank=True)
    themes          = models.JSONField(default=list)        # Gemini-extracted themes
    feature_requests = models.JSONField(default=list)       # Extracted feature requests
    pain_points     = models.JSONField(default=list)
    submitted_at    = models.DateTimeField(auto_now_add=True)

class InsightTheme(models.Model):
    TYPES = [('pain_point','Pain Point'),('feature_request','Feature Request'),
             ('praise','Praise'),('confusion','Confusion')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='clarity_insightthemes')
    theme           = models.CharField(max_length=300)
    theme_type      = models.CharField(max_length=20, choices=TYPES)
    mention_count   = models.IntegerField(default=1)
    priority_score  = models.IntegerField(null=True)        # AI-ranked priority 0–100
    example_quotes  = models.JSONField(default=list)
    first_seen      = models.DateField(auto_now_add=True)
    last_seen       = models.DateField(auto_now=True)

class UserPersona(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='clarity_userpersonas')
    name            = models.CharField(max_length=200)      # e.g. "The Overwhelmed Founder"
    description     = models.TextField()
    goals           = models.JSONField(default=list)
    frustrations    = models.JSONField(default=list)
    behaviours      = models.JSONField(default=list)
    quote           = models.TextField()                    # Representative quote from research
    generated_at    = models.DateTimeField(auto_now_add=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/clarity/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/surveys/` | Create and manage surveys |
| `GET` | `/surveys/{id}/responses/` | Survey responses |
| `POST` | `/surveys/{id}/analyze/` | AI-analyse responses for themes |
| `GET` | `/themes/` | All insight themes |
| `GET` | `/themes/priority/` | Prioritised feature requests |
| `POST` | `/tickets/mine/` | Mine support tickets for insights |
| `GET` | `/personas/` | User personas |
| `POST` | `/personas/generate/` | Generate personas from research |
| `GET` | `/reports/monthly/` | Monthly insight report |
| `GET` | `/analytics/` | Sentiment trend, top themes, NPS drivers |

---

## Section 5: Tech Stack & Delivery

```
pip install requests reportlab django-apscheduler
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Survey builder, response collection, theme extraction, basic report | Weeks 1–5 |
| Phase 2 | Support ticket mining, feature prioritisation, sentiment tracking | Weeks 6–10 |
| Phase 3 | Automated interviews, persona builder, Hotjar integration, monthly report | Weeks 11–15 |

| Tier | Monthly | Responses/mo | Features |
|---|---|---|---|
| Intern | Free | 50 | Surveys + theme extraction |
| Entry | ৳2,000 | 300 | Feature prioritisation, sentiment |
| Mid | ৳5,000 | 1,500 | Ticket mining, personas, monthly report |
| Senior | ৳10,000 | Unlimited | Interviews, Hotjar, full analytics |

*BengalBound HUB — dev branch*
