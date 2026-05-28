# Module Requirements: Content Architect — AI SEO Strategist
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `content_architect` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Google Search Console API, Ahrefs/SEMrush API, Slack, Email

---

## Section 1: Overview

**AI Employee Name:** Content Architect | **Department:** Marketing Operations
**Core Function:** Maps out content calendars, manages keyword lists, audits search visibility indices, tracks target competitor rankings, and generates detailed structural article briefs.
**Value Prop:** *"Your content strategy driven by hard data. Structural SEO briefs created in seconds."*

| | Human SEO Planner | Content Architect AI |
|---|---|---|
| Monthly Cost | ৳35,000–৳55,000 | ৳2,000 |
| Keyword Auditing | Monthly batch reports | Real-time tracking |
| Brief Generation | 1–2 hours per article | 15 seconds per brief |
| Search Console Integration | Manual exports | Automated daily synchronization |

---

## Section 2: Core Capabilities

1. **SEO Keyword Intelligence** — Tracks keywords, search volumes, difficulty ratings, and competitor listings.
2. **Organic Position Tracker** — Synchronizes with Google Search Console to monitor keyword rank improvements and organic click trends.
3. **Structured Outline Generator** — Generates complete editorial outlines (H1, H2, H3 tags, bullet points, core arguments, required keywords) in a side-anchored outline drawer.
4. **Editorial Calendar Planner** — Schedules articles based on seasonal keyword opportunities and domain authority targets.
5. **SEO Competitor Tracker** — Tracks competitor articles ranking for target keywords and identifies keyword gap opportunities.
6. **Cross-Agent Integration** — Sends outline briefs to the copywriter agent (Serea) automatically for draft generation.
7. **Semantic Content Audit** — Audits live web pages for keyword density, layout compliance, and meta-data optimizations.

---

## Section 3: Django Models

```python
from django.db import models

class ContentArchitectConfig(models.Model):
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='architect_configs')
    domain_url       = models.URLField()
    gsc_credentials  = models.JSONField(default=dict, blank=True, help_text="OAuth credentials for Search Console")
    target_competitors = models.JSONField(default=list, blank=True, help_text="Competitor URLs to track")
    is_active        = models.BooleanField(default=True)

class SEOKeyword(models.Model):
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='architect_keywords')
    keyword          = models.CharField(max_length=200)
    search_volume    = models.IntegerField(default=0)
    difficulty       = models.IntegerField(default=0, help_text="0-100 score")
    current_position = models.IntegerField(null=True, blank=True)
    cpc_usd          = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    updated_at       = models.DateTimeField(auto_now=True)

class EditorialBrief(models.Model):
    STATUS_CHOICES = [('draft','Draft'),('outline_ready','Outline Ready'),('sent_to_copywriter','Sent to Copywriter'),('completed','Completed')]
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='architect_briefs')
    target_keyword   = models.ForeignKey(SEOKeyword, on_delete=models.CASCADE)
    title            = models.CharField(max_length=255)
    description      = models.TextField(blank=True)
    outline_json     = models.JSONField(default=dict, help_text="H1/H2/H3 hierarchy and keyword distribution recommendations")
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    publish_by       = models.DateField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/content-architect/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/config/` | View or configure GSC and domain targets |
| `GET/POST` | `/keywords/` | Create or list tracked SEO keywords |
| `POST` | `/keywords/{id}/track-position/` | Update rankings from Google Search Console data |
| `GET/POST` | `/briefs/` | Create and view editorial outlines |
| `POST` | `/briefs/{id}/generate/` | Generate dynamic H1-H3 structural outline from a keyword |
| `POST` | `/briefs/{id}/assign-copywriter/` | Trigger content strategy task to Serea copywriter |
| `GET` | `/analytics/` | Organic rank dynamics, SEO opportunity matrix, traffic charts |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| Search Rankings | Google Search Console API | ✅ FREE |
| Keyword Intel | DataForSEO API (or SEMrush API) | 💲 $20/mo (pay-as-you-go) |
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash | ✅ FREE |
| Task Queue | Celery + Redis | ✅ FREE |

```
pip install google-api-python-client requests
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Keyword database CRUD, Search Console OAuth connection, basic position tracker | Weeks 1–6 |
| Phase 2 | AI Outline briefs generator, competitor tracking tables, side-anchored outline drawer | Weeks 7–12 |
| Phase 3 | SEMrush/Ahrefs integration, copywriter handoff automation, traffic conversion audits | Weeks 13–18 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | Tracked Keywords | Features |
|---|---|---|---|
| Intern | Free | 15 | Keyword CRUD, basic outline briefs |
| Entry | ৳2,000 | 100 | Full outline briefs generator, GSC sync |
| Mid | ৳5,000 | 500 | Competitor tracker, side-anchored drawer, SEMrush integration |
| Senior | ৳10,000 | Unlimited | Copywriter handoff, premium SEO API integrations, semantic audits |

---
*BengalBound HUB — dev branch*
