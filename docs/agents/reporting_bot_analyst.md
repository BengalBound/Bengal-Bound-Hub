# Module Requirements: Reporting Bot — AI Analyst & Reporter
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `reporting_bot` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Google Analytics API, Meta Insights API, HubSpot, Shopify — any data source

---

## Section 1: Overview

**AI Employee Name:** Reporting Bot | **Department:** Business Intelligence
**Target Clients:** Digital marketing agencies needing to send weekly/monthly client reports, SaaS companies tracking KPIs, and any business that currently spends hours compiling reports manually.
**Core Function:** Pulls data from all connected sources, writes AI-powered narrative summaries with insights and recommendations, and auto-generates professional PDF/slide reports — ready to send to clients without any manual work.
**Value Prop:** *"Beautiful client reports, written and designed by AI. Sent every Monday morning automatically."*

| | Human Analyst | Reporting Bot AI |
|---|---|---|
| Monthly Cost | Bundled in salary ৳30,000+ | ৳2,000 |
| Report Prep Time | 4–8 hrs per report | 2 minutes |
| Frequency | Monthly (usually) | Weekly, automated |
| Insight Quality | Dependent on analyst | Consistent, data-driven |

---

## Section 2: Core Capabilities

1. **Multi-Source Data Pull** — Connects to Google Analytics, Meta Ads, Google Ads, HubSpot, Shopify, and custom APIs
2. **AI Narrative Writing** — Gemini writes the "so what" behind the numbers: what improved, what dropped, and why it matters
3. **PDF Report Generation** — Professional branded PDF with charts, tables, KPI cards, and executive summary
4. **Slide Deck Generation** — PowerPoint/Google Slides format for client presentations
5. **Automated Delivery** — Reports emailed to clients automatically on a set schedule (weekly/monthly)
6. **Anomaly Callouts** — AI automatically highlights unusual spikes or drops in the narrative
7. **Custom KPI Dashboard** — Client defines what KPIs matter; Reporting Bot tracks and reports only those

---

## Section 3: Django Models

```python
class ReportConfig(models.Model):
    FREQUENCIES = [('weekly','Weekly'),('biweekly','Bi-Weekly'),('monthly','Monthly')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='reporting_bot_reportconfigs')
    report_name     = models.CharField(max_length(300))
    frequency       = models.CharField(max_length(20), choices=FREQUENCIES)
    send_day        = models.CharField(max_length(20))    # 'monday', '1' (for monthly)
    recipients      = models.JSONField(default=list)      # List of email addresses
    data_sources    = models.JSONField(default=list)      # ['google_analytics', 'meta_ads']
    kpis            = models.JSONField(default=list)      # KPI keys to track
    brand_color     = models.CharField(max_length(7), default='#63DCB8')
    logo_url        = models.URLField(blank=True)
    is_active       = models.BooleanField(default=True)

class DataSource(models.Model):
    SOURCES = [('google_analytics','Google Analytics'),('meta_ads','Meta Ads'),
               ('google_ads','Google Ads'),('hubspot','HubSpot'),
               ('shopify','Shopify'),('custom_api','Custom API')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='reporting_bot_datasources')
    source_type     = models.CharField(max_length(30), choices=SOURCES)
    credentials     = models.JSONField(default=dict)      # Encrypted API credentials
    property_id     = models.CharField(max_length(200), blank=True)
    is_active       = models.BooleanField(default=True)
    last_synced     = models.DateTimeField(null=True)

class Report(models.Model):
    STATUS = [('generating','Generating'),('ready','Ready'),('sent','Sent'),('failed','Failed')]
    config          = models.ForeignKey(ReportConfig, on_delete=models.CASCADE)
    period_start    = models.DateField()
    period_end      = models.DateField()
    raw_data        = models.JSONField(default=dict)
    ai_narrative    = models.TextField(blank=True)        # Gemini-written summary
    pdf_file        = models.FileField(upload_to='reports/client/', null=True)
    slides_file     = models.FileField(upload_to='reports/slides/', null=True)
    status          = models.CharField(max_length(20), choices=STATUS, default='generating')
    generated_at    = models.DateTimeField(null=True)
    sent_at         = models.DateTimeField(null=True)
    opened_count    = models.IntegerField(default=0)

class KPISnapshot(models.Model):
    report          = models.ForeignKey(Report, on_delete=models.CASCADE)
    kpi_name        = models.CharField(max_length(200))
    value_current   = models.FloatField()
    value_previous  = models.FloatField()
    change_pct      = models.FloatField()
    is_anomaly      = models.BooleanField(default=False)
    anomaly_note    = models.TextField(blank=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/reporting-bot/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/configs/` | Manage report configurations |
| `GET/POST` | `/data-sources/` | Connect analytics sources |
| `POST` | `/reports/generate/` | Trigger report generation now |
| `GET` | `/reports/` | List all generated reports |
| `GET` | `/reports/{id}/` | Report detail + preview |
| `GET` | `/reports/{id}/pdf/` | Download PDF report |
| `POST` | `/reports/{id}/send/` | Send report to recipients |
| `GET` | `/kpis/{report_id}/` | KPI snapshots with change % |
| `GET` | `/analytics/` | Open rates, delivery stats, KPI trends |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash | ✅ FREE |
| Google Analytics | GA4 Data API | ✅ FREE |
| Meta Insights | Meta Marketing API | ✅ FREE |
| PDF Generation | `reportlab` + `matplotlib` | ✅ FREE |
| Slides Export | `python-pptx` | ✅ FREE |
| Chart Generation | `matplotlib` / `plotly` | ✅ FREE |
| Task Queue | `django-apscheduler` | ✅ FREE |
| Email | Gmail SMTP | ✅ FREE |

```
pip install google-analytics-data reportlab matplotlib python-pptx django-apscheduler
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Google Analytics + Meta Ads data pull, Gemini narrative, PDF report, manual send | Weeks 1–6 |
| Phase 2 | Automated scheduling, Google Ads + HubSpot, branded PDF templates, email delivery | Weeks 7–12 |
| Phase 3 | Slide deck export, Shopify integration, custom KPI builder, open-rate tracking | Weeks 13–18 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | Reports/mo | Data Sources | Features |
|---|---|---|---|---|
| Intern | Free | 2 | 1 | Basic PDF, manual send |
| Entry | ৳2,000 | 8 | 3 | Automated delivery, AI narrative |
| Mid | ৳5,000 | 25 | 6 | Slides export, anomaly callouts, branding |
| Senior | ৳10,000 | Unlimited | All | White-label, custom KPI builder, open tracking |

---
*BengalBound HUB — dev branch*
