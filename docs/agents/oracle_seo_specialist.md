# Module Requirements: Oracle — AI SEO Specialist
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `oracle` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Google Search Console API, Google Analytics 4, Ahrefs API, Semrush API, WordPress REST API

---

## Section 1: Overview

**AI Employee Name:** Oracle | **Department:** Search & Visibility
**Target Clients:** Digital agencies managing SEO for clients, e-commerce stores, SaaS companies, and any business that wants to rank higher on Google without a full-time SEO team.
**Core Function:** Performs full technical SEO audits, builds keyword strategies, tracks rankings daily, fixes on-page issues automatically, and delivers monthly SEO reports — all without a human SEO specialist.
**Value Prop:** *"Page 1 rankings, automated. No agency retainer. No SEO guesswork."*

| | Human SEO Specialist | Oracle AI |
|---|---|---|
| Monthly Cost | ৳30,000–৳50,000 | ৳2,000 |
| Audit Frequency | Monthly (at best) | Weekly automated |
| Keyword Research | Days | Minutes |
| Rank Tracking | Manual spreadsheet | Daily automated |
| On-page Fixes | Slow, billed hourly | Immediate + applied |

---

## Section 2: Core Capabilities

1. **Technical SEO Audit** — Crawls the website for: broken links, missing meta tags, duplicate content, slow pages, missing schema, mobile issues, Core Web Vitals
2. **Keyword Research** — Discovers high-opportunity keywords based on industry, competitor gaps, and search volume trends
3. **On-Page Optimizer** — Rewrites title tags, meta descriptions, H1/H2 structure, and internal links using Gemini
4. **Daily Rank Tracker** — Tracks keyword positions in Google daily; alerts on significant rank changes
5. **Competitor Gap Analysis** — Identifies keywords competitors rank for that the client doesn't — prioritized opportunity list
6. **Backlink Monitor** — Tracks new and lost backlinks; alerts on toxic links; suggests link-building opportunities
7. **Content Gap Report** — Identifies topics with search demand that the client has no content for; generates content briefs
8. **Monthly SEO Report** — PDF with ranking improvements, traffic changes, fixes applied, and next-month priorities

---

## Section 3: Django Models

```python
class Website(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='oracle_websites')
    domain          = models.URLField()
    gsc_property    = models.CharField(max_length=300, blank=True)  # Google Search Console property
    ga4_property    = models.CharField(max_length=100, blank=True)
    cms             = models.CharField(max_length=50, blank=True)   # 'wordpress', 'custom'
    wordpress_url   = models.URLField(blank=True)
    wp_api_key      = models.TextField(blank=True)
    last_crawled    = models.DateTimeField(null=True)

class SEOIssue(models.Model):
    TYPES = [('missing_meta','Missing Meta'),('broken_link','Broken Link'),
             ('duplicate_content','Duplicate Content'),('slow_page','Slow Page'),
             ('missing_schema','Missing Schema'),('mobile_issue','Mobile Issue'),
             ('missing_alt','Missing Image Alt')]
    SEVERITY = [('critical','Critical'),('warning','Warning'),('info','Info')]
    STATUS = [('open','Open'),('fixed','Fixed'),('ignored','Ignored')]
    website         = models.ForeignKey(Website, on_delete=models.CASCADE)
    issue_type      = models.CharField(max_length=30, choices=TYPES)
    severity        = models.CharField(max_length=10, choices=SEVERITY)
    page_url        = models.URLField()
    description     = models.TextField()
    fix_suggestion  = models.TextField()    # Gemini-generated fix
    auto_fixed      = models.BooleanField(default=False)
    status          = models.CharField(max_length=10, choices=STATUS, default='open')
    found_at        = models.DateTimeField(auto_now_add=True)
    fixed_at        = models.DateTimeField(null=True)

class Keyword(models.Model):
    website         = models.ForeignKey(Website, on_delete=models.CASCADE)
    keyword         = models.CharField(max_length=500)
    search_volume   = models.IntegerField(null=True)
    difficulty      = models.IntegerField(null=True)    # 0–100
    current_rank    = models.IntegerField(null=True)
    previous_rank   = models.IntegerField(null=True)
    target_page     = models.URLField(blank=True)
    is_tracking     = models.BooleanField(default=True)
    last_checked    = models.DateTimeField(null=True)

class RankHistory(models.Model):
    keyword         = models.ForeignKey(Keyword, on_delete=models.CASCADE)
    rank            = models.IntegerField()
    checked_at      = models.DateField()

class Backlink(models.Model):
    STATUS = [('active','Active'),('lost','Lost'),('toxic','Toxic')]
    website         = models.ForeignKey(Website, on_delete=models.CASCADE)
    source_url      = models.URLField()
    target_url      = models.URLField()
    domain_authority = models.IntegerField(null=True)
    anchor_text     = models.CharField(max_length=500, blank=True)
    status          = models.CharField(max_length=10, choices=STATUS, default='active')
    first_seen      = models.DateField()
    last_seen       = models.DateField()
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/oracle/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/websites/` | Manage connected websites |
| `POST` | `/websites/{id}/audit/` | Trigger full technical SEO audit |
| `GET` | `/issues/` | List all SEO issues |
| `POST` | `/issues/{id}/fix/` | Apply AI-generated fix |
| `GET` | `/keywords/` | Keyword tracking list |
| `POST` | `/keywords/research/` | Run keyword research for a topic |
| `GET` | `/rankings/` | Daily rank positions |
| `GET` | `/rankings/changes/` | Significant rank changes (±5 positions) |
| `GET` | `/backlinks/` | Backlink profile |
| `GET` | `/backlinks/toxic/` | Toxic backlinks to disavow |
| `GET` | `/competitor-gaps/` | Competitor keyword gap opportunities |
| `GET` | `/content-gaps/` | Missing content topics with demand |
| `GET` | `/reports/monthly/` | Monthly SEO PDF report |
| `GET` | `/analytics/` | Traffic, rankings, issues fixed trends |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash | ✅ FREE |
| Crawling | `scrapy` or `requests` + `beautifulsoup4` | ✅ FREE |
| Google Search Console | GSC API | ✅ FREE |
| Google Analytics | GA4 Data API | ✅ FREE |
| Rank Tracking | ValueSERP API or custom Google scraper | 💲 ~$50/mo |
| Backlinks | Ahrefs API or Moz API | 💲 $99/mo |
| PDF Reports | `reportlab` | ✅ FREE |
| Task Queue | `django-apscheduler` | ✅ FREE |

```
pip install scrapy beautifulsoup4 requests reportlab google-analytics-data django-apscheduler
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Technical audit (crawler), issue detection, on-page fix suggestions, keyword tracking | Weeks 1–6 |
| Phase 2 | GSC + GA4 integration, daily rank tracking, competitor gap, monthly PDF report | Weeks 7–12 |
| Phase 3 | Auto-fix via WordPress API, backlink monitoring, content gap briefs, Ahrefs integration | Weeks 13–18 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | Keywords | Features |
|---|---|---|---|
| Intern | Free | 10 | Basic audit, issue list |
| Entry | ৳2,000 | 50 | Rank tracking, on-page suggestions |
| Mid | ৳5,000 | 200 | Competitor gaps, monthly report, GSC |
| Senior | ৳10,000 | Unlimited | Auto-fix, backlinks, content briefs |

---
*BengalBound HUB — dev branch*
