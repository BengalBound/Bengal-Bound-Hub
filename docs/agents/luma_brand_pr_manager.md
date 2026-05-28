# Module Requirements: Luma — AI Brand Manager & PR Monitor
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `luma` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)

---

## Section 1: Overview

**AI Employee Name:** Luma | **Department:** Brand & Communications
**Core Function:** Monitors all brand mentions across the internet in real time, scores sentiment, manages press release distribution, drafts PR responses, and protects brand reputation around the clock.
**Value Prop:** *"Your brand reputation monitored 24/7. Crisis caught in minutes, not days."*

---

## Section 2: Core Capabilities

1. **Brand Mention Monitor** — Tracks brand name, product names, and key executives across news, social media, forums, review sites, and blogs
2. **Sentiment Scoring** — Each mention scored positive/neutral/negative with urgency classification
3. **Reputation Crisis Alert** — If negative mention volume spikes or a high-reach negative post appears, immediate alert with AI response draft
4. **Press Release Drafting** — Gemini drafts press releases for product launches, milestones, and responses
5. **Media Contact Database** — Maintains list of journalists and outlets relevant to the client's industry for PR outreach
6. **Review Management** — Monitors Google Reviews, Trustpilot, G2 — drafts responses to both positive and negative reviews
7. **Monthly Brand Health Report** — Mention volume, sentiment trend, top sources, reach estimate, share of voice

---

## Section 3: Django Models

```python
class BrandConfig(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='luma_brandconfigs')
    brand_name      = models.CharField(max_length=300)
    aliases         = models.JSONField(default=list)    # Alternative spellings/abbreviations
    key_people      = models.JSONField(default=list)    # CEO name, founders to monitor
    industry        = models.CharField(max_length=200)
    crisis_threshold = models.IntegerField(default=5)   # Negative mentions/hour to trigger crisis

class BrandMention(models.Model):
    SENTIMENT = [('positive','Positive'),('neutral','Neutral'),('negative','Negative')]
    URGENCY   = [('low','Low'),('medium','Medium'),('high','High'),('crisis','Crisis')]
    SOURCES   = [('news','News'),('twitter','Twitter/X'),('reddit','Reddit'),
                 ('review','Review Site'),('blog','Blog'),('forum','Forum')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='luma_brandmentions')
    source          = models.CharField(max_length=20, choices=SOURCES)
    url             = models.URLField()
    title           = models.CharField(max_length=500, blank=True)
    snippet         = models.TextField()
    sentiment       = models.CharField(max_length=10, choices=SENTIMENT)
    urgency         = models.CharField(max_length=10, choices=URGENCY)
    reach_estimate  = models.IntegerField(null=True)    # Estimated audience size
    ai_summary      = models.TextField(blank=True)
    response_draft  = models.TextField(blank=True)      # Gemini-drafted response
    responded       = models.BooleanField(default=False)
    alert_sent      = models.BooleanField(default=False)
    detected_at     = models.DateTimeField(auto_now_add=True)

class PressRelease(models.Model):
    STATUS = [('draft','Draft'),('approved','Approved'),('distributed','Distributed')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='luma_pressreleases')
    headline        = models.CharField(max_length=500)
    body            = models.TextField()
    boilerplate     = models.TextField()
    status          = models.CharField(max_length=20, choices=STATUS, default='draft')
    distributed_at  = models.DateTimeField(null=True)
    generated_at    = models.DateTimeField(auto_now_add=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/luma/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/config/` | Brand monitoring config |
| `GET` | `/mentions/` | All brand mentions |
| `GET` | `/mentions/negative/` | Negative mentions only |
| `GET` | `/mentions/crisis/` | Active crisis-level alerts |
| `POST` | `/mentions/{id}/respond/` | Mark responded + log channel |
| `POST` | `/press-releases/generate/` | AI-draft press release |
| `GET` | `/press-releases/` | All press releases |
| `GET` | `/reviews/` | Aggregated review monitoring |
| `GET` | `/reports/monthly/` | Monthly brand health report |
| `GET` | `/analytics/` | Sentiment trend, mention volume, reach |

---

## Section 5: Tech Stack & Delivery

```
pip install requests beautifulsoup4 newsapi-python praw tweepy reportlab
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | News + social monitoring, sentiment scoring, crisis alerts, response drafts | Weeks 1–5 |
| Phase 2 | Review monitoring, press release generator, monthly report, reach estimation | Weeks 6–11 |
| Phase 3 | Media contact database, PR distribution, share of voice, executive monitoring | Weeks 12–16 |

| Tier | Monthly | Features |
|---|---|---|
| Intern | Free | News monitoring, basic alerts |
| Entry | ৳2,000 | Social tracking, response drafts |
| Mid | ৳5,000 | Review mgmt, press release, monthly report |
| Senior | ৳10,000 | Media contacts, PR distribution, full analytics |

*BengalBound HUB — dev branch*
