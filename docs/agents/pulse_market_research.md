# Module Requirements: Pulse — AI Market Research Analyst
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `pulse` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Google Trends, Reddit API, Twitter/X API, News APIs

---

## Section 1: Overview

**AI Employee Name:** Pulse | **Department:** Strategy & Research
**Core Function:** Monitors industry trends, consumer sentiment, and market signals across social media, news, and search data — delivering weekly research briefs, opportunity alerts, and competitive landscape summaries.
**Value Prop:** *"Know your market before your competitors do. Pulse watches 20+ sources so you don't have to."*

| | Human Market Researcher | Pulse AI |
|---|---|---|
| Monthly Cost | ৳35,000–৳60,000 | ৳2,000 |
| Research Cycle | Monthly | Weekly automated |
| Data Sources | 3–5 | 20+ |
| Insight Speed | Days | Hours |

---

## Section 2: Core Capabilities

1. **Trend Detection** — Google Trends, Reddit, Twitter/X, industry forums — emerging topics in client's space
2. **Consumer Sentiment Analysis** — Real-time sentiment tracking on brand mentions and industry keywords
3. **Market Sizing Estimates** — Public data used to estimate TAM/SAM for target market
4. **Weekly Research Brief** — 1-page Gemini-written summary: top 3 trends, opportunities, threats, recommendations
5. **Opportunity Alerts** — Instant notification on high-signal events (viral trend, competitor failure, new regulation)
6. **Survey Builder & Analyzer** — Creates and distributes surveys; Gemini analyses responses for insights
7. **Industry News Digest** — Daily digest of top articles, summarised with relevance scoring

---

## Section 3: Django Models

```python
class ResearchConfig(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='pulse_researchconfigs')
    industry        = models.CharField(max_length=200)
    keywords        = models.JSONField(default=list)
    competitors     = models.JSONField(default=list)
    target_markets  = models.JSONField(default=list)
    alert_threshold = models.IntegerField(default=70)

class TrendSignal(models.Model):
    TYPES = [('trend','Rising Trend'),('sentiment_shift','Sentiment Shift'),
             ('news_event','News Event'),('opportunity','Opportunity'),('threat','Threat')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='pulse_trendsignals')
    signal_type     = models.CharField(max_length=30, choices=TYPES)
    keyword         = models.CharField(max_length=300)
    source          = models.CharField(max_length=50)
    strength        = models.IntegerField()
    summary         = models.TextField()
    detected_at     = models.DateTimeField(auto_now_add=True)
    alert_sent      = models.BooleanField(default=False)

class ResearchReport(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='pulse_researchreports')
    period          = models.CharField(max_length=50)
    narrative       = models.TextField()
    key_findings    = models.JSONField(default=list)
    opportunities   = models.JSONField(default=list)
    threats         = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    pdf_file        = models.FileField(upload_to='reports/pulse/', null=True)
    generated_at    = models.DateTimeField(auto_now_add=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/pulse/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/config/` | Research configuration |
| `GET` | `/signals/` | All detected signals |
| `GET` | `/signals/alerts/` | High-strength alerts only |
| `POST` | `/reports/generate/` | Generate research report now |
| `GET` | `/news/digest/` | Today's industry news digest |
| `POST` | `/surveys/create/` | Build and send market survey |
| `GET` | `/surveys/{id}/results/` | Survey results + AI analysis |

---

## Section 5: Tech Stack & Delivery

```
pip install pytrends praw tweepy newsapi-python reportlab
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Google Trends, Reddit, weekly brief, news digest | Weeks 1–5 |
| Phase 2 | Sentiment analysis, Twitter/X, opportunity alerts, PDFs | Weeks 6–11 |
| Phase 3 | Survey builder, market sizing, real-time alerts | Weeks 12–16 |

| Tier | Monthly | Features |
|---|---|---|
| Intern | Free | Weekly brief + news digest |
| Entry | ৳2,000 | Trend alerts, sentiment analysis |
| Mid | ৳5,000 | Survey builder, opportunity reports |
| Senior | ৳10,000 | Real-time alerts, market sizing, all sources |

*BengalBound HUB — dev branch*
