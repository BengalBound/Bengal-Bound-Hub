# Module Requirements: Serea — AI Copywriter & Content Strategist
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `serea_content` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Google Sheets API, Google Drive API, HubSpot, WordPress REST API, Meta Graph API

---

## Section 1: Overview

**AI Employee Name:** Serea Content | **Department:** Marketing & Communications
**Core Function:** Automates marketing copy creation, drafted scheduled blogs, operates scheduled newsletters, runs inline A/B testing variations, and updates drafts based on outline briefs from Content Architect.
**Value Prop:** *"Beautiful, high-ranking copy drafted automatically. Your editorial queue always full."*

| | Human Copywriter | Serea Content AI |
|---|---|---|
| Monthly Cost | ৳30,000–৳50,000 | ৳2,000 |
| Article Drafting | 1–3 days per draft | 30 seconds per draft |
| Optimization | Intuitive, manual | AI-optimized matching briefs |
| A/B Testing | Periodic setups | Infinite inline variations |

---

## Section 2: Core Capabilities

1. **Content Brief Processing** — Automatically consumes SEO outline briefs from the Content Architect to draft optimized copy.
2. **Scheduled Blog Creator** — Connects directly to WordPress or custom CMS APIs to draft, schedule, and categorize blog articles.
3. **Copywriting Sequencer** — Schedules marketing campaigns across platforms (Facebook, Instagram, LinkedIn, Newsletters).
4. **Dynamic A/B Testing Variations** — Automatically generates 3 variations of any copy (e.g. creative, direct, humorous) to let users toggle.
5. **Inline Editor Widget** — Rich Text Editor integration allowing users to click "Refine with AI" or "Adjust Tone" for any paragraph.
6. **SEO Keyword Density Validator** — Analyzes drafts in real-time, verifying matching keyword distributions from target brief.
7. **Asset Link Binder** — Binds drafts with media links from Google Drive folders automatically.

---

## Section 3: Django Models

```python
from django.db import models

class SereaContentConfig(models.Model):
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='sereacontent_configs')
    default_tone     = models.CharField(max_length=50, default='professional')  # playful, professional, bold
    wordpress_url    = models.URLField(blank=True)
    wordpress_user   = models.CharField(max_length=100, blank=True)
    wordpress_token  = models.TextField(blank=True)       # Encrypted
    is_active        = models.BooleanField(default=True)

class ContentPiece(models.Model):
    STATUS_CHOICES = [('draft','Draft'),('scheduled','Scheduled'),('published','Published'),('failed','Failed')]
    TYPE_CHOICES = [('blog','Blog Post'),('social','Social Post'),('newsletter','Newsletter')]
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='sereacontent_pieces')
    title            = models.CharField(max_length=255)
    type             = models.CharField(max_length=20, choices=TYPE_CHOICES)
    body_content     = models.TextField()
    variations       = models.JSONField(default=dict, help_text="A/B variations: {'variant_a': '...', 'variant_b': '...'}")
    keyword_matches  = models.JSONField(default=dict, help_text="Density verification analysis")
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    publish_at       = models.DateTimeField(null=True, blank=True)
    wordpress_id     = models.IntegerField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/serea-content/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/config/` | View or configure tone rules and WordPress/CMS keys |
| `GET/POST` | `/pieces/` | Create or view draft content pieces |
| `POST` | `/pieces/draft-from-brief/` | Draft copy automatically consuming a Content Architect Brief |
| `POST` | `/pieces/{id}/refine/` | Refine selection using AI (adjust tone, shorten, lengthen) |
| `POST` | `/pieces/{id}/ab-variations/` | Generate A/B copy variations |
| `POST` | `/pieces/{id}/publish/` | Manually push piece to WordPress or social networks |
| `GET` | `/analytics/` | Word counts, scheduled items overview, A/B performance |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| Publishing REST API | WordPress REST API | ✅ FREE |
| Social Sync | Meta Graph API (Pages, Instagram) | ✅ FREE |
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash | ✅ FREE |
| Task Queue | Celery + Redis | ✅ FREE |

```
pip install requests beautifulsoup4
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Content pieces CRUD, basic Gemini drafting, tone selection settings | Weeks 1–6 |
| Phase 2 | WordPress REST API synchronization, keyword density calculator, A/B variation overlays | Weeks 7–12 |
| Phase 3 | Inline editor integration, SEO Content Architect brief consumption, dynamic newsletters campaigns | Weeks 13–18 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | Drafts/mo | Features |
|---|---|---|---|
| Intern | Free | 5 | Tone selection, basic drafting |
| Entry | ৳2,000 | 30 | Brief-to-draft conversion, SEO density checker |
| Mid | ৳5,000 | 100 | WordPress publish integration, A/B variations, inline refiner |
| Senior | ৳10,000 | Unlimited | Auto-newsletters, premium CMS connectors, full asset binder |

---
*BengalBound HUB — dev branch*
