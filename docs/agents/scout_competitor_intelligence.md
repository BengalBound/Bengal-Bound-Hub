# Module Requirements: Scout — AI Competitor Intelligence Analyst
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `scout` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)

---

## Section 1: Overview

**AI Employee Name:** Scout | **Department:** Strategy
**Core Function:** Continuously monitors competitors' websites, pricing, product launches, job postings, ads, and social media — alerting clients the moment a competitor makes a significant move.
**Value Prop:** *"Know what your competitor just did before your sales team's morning standup."*

---

## Section 2: Core Capabilities

1. **Website Change Detection** — Weekly crawl of competitor sites; alerts on pricing changes, new features, new pages
2. **Ad Intelligence** — Monitors competitor Facebook/Google ads via Meta Ad Library and SimilarWeb
3. **Job Posting Monitor** — Tracks competitor hiring — what they're building is revealed by who they hire
4. **Social Media Tracker** — Monitors competitor posts, engagement, and campaign launches
5. **Pricing Intelligence** — Tracks competitor pricing pages; alerts on any price change
6. **Product Launch Alerts** — Detects new product announcements via press releases, Product Hunt, and news
7. **Weekly Battlecard** — Gemini-generated competitive battlecard: their strengths, weaknesses, positioning, and your counter-strategy
8. **Share of Voice Analysis** — Compares brand mention volume across social and news vs competitors

---

## Section 3: Django Models

```python
class Competitor(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='scout_competitors')
    name            = models.CharField(max_length=300)
    website         = models.URLField()
    pricing_url     = models.URLField(blank=True)
    linkedin_url    = models.URLField(blank=True)
    facebook_page   = models.URLField(blank=True)
    twitter_handle  = models.CharField(max_length=100, blank=True)
    is_active       = models.BooleanField(default=True)
    last_checked    = models.DateTimeField(null=True)

class CompetitorChange(models.Model):
    TYPES = [('pricing','Pricing Change'),('product','New Product/Feature'),
             ('hiring','New Hiring Signal'),('ad','New Ad Campaign'),
             ('content','Content/Message Shift'),('pr','Press Release')]
    IMPACT = [('low','Low'),('medium','Medium'),('high','High')]
    competitor      = models.ForeignKey(Competitor, on_delete=models.CASCADE)
    change_type     = models.CharField(max_length=20, choices=TYPES)
    impact          = models.CharField(max_length=10, choices=IMPACT)
    description     = models.TextField()
    ai_analysis     = models.TextField()        # Gemini: what this means + recommended response
    source_url      = models.URLField(blank=True)
    detected_at     = models.DateTimeField(auto_now_add=True)
    alert_sent      = models.BooleanField(default=False)

class Battlecard(models.Model):
    competitor      = models.ForeignKey(Competitor, on_delete=models.CASCADE)
    strengths       = models.JSONField(default=list)
    weaknesses      = models.JSONField(default=list)
    positioning     = models.TextField()
    counter_strategy = models.TextField()
    pricing_summary = models.TextField()
    generated_at    = models.DateTimeField(auto_now_add=True)
    pdf_file        = models.FileField(upload_to='reports/scout/', null=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/scout/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/competitors/` | Manage competitor list |
| `GET` | `/changes/` | All detected changes |
| `GET` | `/changes/high-impact/` | High-impact changes only |
| `POST` | `/competitors/{id}/scan/` | Force competitor scan now |
| `GET` | `/competitors/{id}/battlecard/` | Latest battlecard |
| `POST` | `/competitors/{id}/battlecard/generate/` | Regenerate battlecard |
| `GET` | `/share-of-voice/` | Brand mention volume comparison |
| `GET` | `/analytics/` | Change frequency, top competitors, alert history |

---

## Section 5: Tech Stack & Delivery

```
pip install requests beautifulsoup4 scrapy reportlab django-apscheduler
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Website change detection, pricing tracker, weekly alert email | Weeks 1–5 |
| Phase 2 | Job posting monitor, social tracker, Meta Ad Library, battlecard | Weeks 6–10 |
| Phase 3 | Share of voice, SimilarWeb integration, Product Hunt monitor | Weeks 11–16 |

| Tier | Monthly | Competitors | Features |
|---|---|---|---|
| Intern | Free | 2 | Website + pricing alerts |
| Entry | ৳2,000 | 5 | Social tracking, battlecard |
| Mid | ৳5,000 | 15 | Ad intelligence, job signals |
| Senior | ৳10,000 | Unlimited | Share of voice, full dashboard |

*BengalBound HUB — dev branch*
