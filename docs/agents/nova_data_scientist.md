# Module Requirements: Nova — AI Data Scientist & BI Analyst
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `nova` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Google BigQuery, PostgreSQL, MySQL, Shopify, HubSpot, REST data sources

---

## Section 1: Overview

**AI Employee Name:** Nova | **Department:** Data Science & Business Intelligence
**Target Clients:** E-commerce brands, SaaS companies, agencies, and any data-rich business that needs insights but can't afford a full-time data scientist or BI analyst.
**Core Function:** Connects to all data sources, runs automated analysis, discovers hidden patterns and trends, builds visual dashboards, and delivers plain-English insight reports — no SQL or Python required from the client.
**Value Prop:** *"Your data speaks. Nova listens and tells you exactly what it means."*

---

## Section 2: Core Capabilities

1. **Multi-Source Data Connector** — Connects to SQL databases, Google Sheets, Shopify, HubSpot, GA4, and custom APIs
2. **Natural Language Querying** — Client types "What was our best-performing product last quarter?" — Nova queries the data and answers
3. **Automated Anomaly Detection** — Continuously monitors key metrics; alerts when something unusual happens
4. **Cohort & Funnel Analysis** — Analyzes customer cohorts, conversion funnels, churn rates, and LTV automatically
5. **Predictive Forecasting** — Forecasts revenue, churn, inventory demand using statistical models (Prophet, linear regression)
6. **Insight Report Generation** — Weekly AI-written narrative: what the data showed, what changed, what to do about it
7. **Interactive Dashboard Builder** — Generates embeddable dashboard widgets from any data source
8. **A/B Test Analyzer** — Upload experiment results; Nova calculates statistical significance and recommends winner

---

## Section 3: Django Models

```python
class DataSource(models.Model):
    TYPES = [('postgresql','PostgreSQL'),('mysql','MySQL'),('bigquery','BigQuery'),
             ('google_sheets','Google Sheets'),('shopify','Shopify'),
             ('hubspot','HubSpot'),('rest_api','REST API')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='nova_datasources')
    name            = models.CharField(max_length=300)
    source_type     = models.CharField(max_length=20, choices=TYPES)
    credentials     = models.JSONField(default=dict)    # Encrypted connection details
    schema_cache    = models.JSONField(default=dict)    # Cached table/column list
    is_active       = models.BooleanField(default=True)
    last_synced     = models.DateTimeField(null=True)

class DataQuery(models.Model):
    STATUS = [('pending','Pending'),('running','Running'),('completed','Completed'),('failed','Failed')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='nova_dataqueries')
    natural_question = models.TextField()               # User's plain-English question
    generated_sql   = models.TextField(blank=True)      # Gemini-generated SQL
    result_data     = models.JSONField(default=list)
    result_summary  = models.TextField(blank=True)      # Gemini plain-English answer
    chart_type      = models.CharField(max_length=50, blank=True)
    status          = models.CharField(max_length=20, choices=STATUS, default='pending')
    created_at      = models.DateTimeField(auto_now_add=True)

class MetricAlert(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='nova_metricalerts')
    metric_name     = models.CharField(max_length=300)
    data_source     = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    query           = models.TextField()                # SQL to fetch metric
    threshold_type  = models.CharField(max_length=20)  # 'drops_by', 'exceeds', 'below'
    threshold_value = models.FloatField()
    is_active       = models.BooleanField(default=True)
    last_triggered  = models.DateTimeField(null=True)

class InsightReport(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='nova_insightreports')
    period          = models.CharField(max_length=50)   # 'weekly', 'monthly'
    narrative       = models.TextField()
    key_findings    = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    pdf_file        = models.FileField(upload_to='reports/nova/', null=True)
    generated_at    = models.DateTimeField(auto_now_add=True)
    sent_at         = models.DateTimeField(null=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/nova/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/data-sources/` | Connect data sources |
| `POST` | `/query/` | Natural language data query |
| `GET` | `/queries/` | Query history |
| `POST` | `/alerts/` | Set metric anomaly alerts |
| `GET` | `/alerts/triggered/` | Recent alert triggers |
| `POST` | `/forecast/` | Revenue/churn/demand forecast |
| `POST` | `/ab-test/analyze/` | A/B test significance analysis |
| `GET` | `/reports/weekly/` | Latest insight report |
| `POST` | `/reports/generate/` | Generate report now |
| `GET` | `/dashboard/widgets/` | Dashboard widget data |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash (NL→SQL, narratives) | ✅ FREE |
| SQL Execution | `sqlalchemy`, `psycopg2`, `PyMySQL` | ✅ FREE |
| BigQuery | `google-cloud-bigquery` | 💲 $5/TB processed |
| Forecasting | `prophet` (Meta's forecasting library) | ✅ FREE |
| Charts | `matplotlib`, `plotly` | ✅ FREE |
| Sheets | `gspread` | ✅ FREE |
| Task Queue | `django-apscheduler` | ✅ FREE |

```
pip install sqlalchemy psycopg2-binary prophet plotly gspread google-cloud-bigquery
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery & Pricing

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | PostgreSQL/MySQL connect, NL query, result + summary, basic charts | Weeks 1–6 |
| Phase 2 | Metric alerts, cohort analysis, weekly insight report, BigQuery | Weeks 7–12 |
| Phase 3 | Forecasting (Prophet), A/B analyzer, dashboard builder, Shopify/HubSpot | Weeks 13–20 |

| Tier | Monthly | Queries/mo | Features |
|---|---|---|---|
| Intern | Free | 20 | NL query, basic charts |
| Entry | ৳2,000 | 100 | Metric alerts, insight report |
| Mid | ৳5,000 | 500 | Forecasting, cohort analysis, BigQuery |
| Senior | ৳10,000 | Unlimited | A/B testing, dashboard builder, all sources |

---
*BengalBound HUB — dev branch*
