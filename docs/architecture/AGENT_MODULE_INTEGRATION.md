# Agent ↔ Module Integration & External Deployment Guide

## Overview

BengalBound HUB's 33 AI Agents and 83 Business Modules are two independent layers that work together. This document explains how they integrate, and how any agent can be deployed outside the HUB entirely.

---

## Integration Model

```
┌─────────────────────────────────────────────────────────────┐
│                    BengalBound HUB                          │
│                                                             │
│  ┌─────────────────┐     reads/writes     ┌─────────────┐  │
│  │   AI Agents      │ ──────────────────▶ │   Modules   │  │
│  │  (agents/<name>) │                     │(modules/<m>)│  │
│  │                  │ ◀────────────────── │             │  │
│  │  engine.py       │   Django ORM queries│  CRM, HR,   │  │
│  │  tasks.py        │   shared database   │  Payroll,   │  │
│  │  signals.py      │                     │  Ecommerce  │  │
│  │  webhooks.py     │                     │  etc.       │  │
│  └─────────────────┘                     └─────────────┘  │
│           │                                                 │
│           │  agent_chat() → LiteLLM Proxy → Any LLM        │
│           │  AgentLog, AgentMemory, AgentPermissionRequest  │
│           │  AgentIntegration (encrypted external creds)    │
└───────────┼─────────────────────────────────────────────────┘
            │
            │  REST API   /hub/<slug>/agents/<agent>/
            │  Inbound Webhook  /agents/webhook/<token>/
            │  Celery Beat  (runs autonomously)
            ▼
     Any External System
  (Shopify, GitHub, Slack, Twilio,
   HeyGen, Recall.ai, DocuSign...)
```

---

## Agent Skills & Platform Capabilities

Each agent is a full mini-platform with its own specialised skills and external integrations — not a generic AI running on top of a shared engine.

### Aria — Customer Support Platform
**Skills:** Ticket resolution, SLA enforcement, escalation routing, KB article generation, sentiment analysis
**Integrations:** Email gateway (inbound tickets), Slack (breach alerts), CRM module
**Autonomous:** Resolves low-priority tickets every 4 hours; flags SLA breaches every 30 minutes
**Confidence gate:** If resolution confidence < 0.8, pauses and emails owner for approval

### Atlas — Executive Assistant Platform
**Skills:** Meeting briefing generation, task extraction from text, priority scoring, morning briefings
**Integrations:** Google Calendar (via AgentIntegration), Business Calendar module, Task Board module
**Autonomous:** Daily 9am briefing from calendar + tasks; overdue task alerts; weekly executive summary

### Babel — Translation Platform
**Skills:** Multi-language translation, quality review, language detection, domain glossary building
**Integrations:** Documents module, Announcements module, Email Marketing module
**Autonomous:** Translation queue processing every hour; retry failed jobs weekly

### Cash — Payroll Processing Platform
**Skills:** Payroll narrative generation, net pay calculation, anomaly detection, compliance checks
**Integrations:** Payroll module, HR module, Accounting module
**Autonomous:** Monthly payroll reminder on day 25; anomaly checks against all businesses daily

### Chloe (Video Concierge) — Live Video AI Platform
**Skills:** Real-time video conversation, session type routing (support/onboarding/sales), transcript analysis, outcome tracking
**Integrations:** HeyGen/D-ID WebRTC API, Booking module, CRM module, Video Meet module
**Autonomous:** Daily session digest; WebRTC session state managed via inbound webhooks
**Inbound webhook:** HeyGen/D-ID session state callbacks → `/agents/webhook/<token>/`

### Clarity — Feedback Intelligence Platform
**Skills:** Survey theme extraction, sentiment scoring, emotion analysis, urgency detection, weekly insight reports
**Integrations:** Forms Builder module, Data Collection module, Reports module
**Autonomous:** Theme extraction runs after each survey batch; weekly insight digest

### Concierge — Client Concierge Platform
**Skills:** Email triage and routing, meeting scheduling, reply drafting, lead qualification
**Integrations:** Business Calendar module, CRM module, Email Marketing module
**Autonomous:** Daily inbox digest; meeting scheduling from inbound requests

### Content Architect — Content Strategy Platform
**Skills:** Multi-channel content generation (blog, email, social, video, ads), SEO optimisation, calendar planning, content repurposing
**Integrations:** Website module, Email Marketing module, Slides module
**Autonomous:** Weekly content calendar audit; SEO gap analysis

### Crux — CRM Platform
**Skills:** Contact intent scoring, follow-up sequence generation, pipeline health reporting, re-engagement messaging
**Integrations:** CRM module, Leads module, Deal Flow module, Invoicing module
**Autonomous:** Contact scoring runs daily; weekly pipeline health report

### Dox — Technical Writing Platform
**Skills:** API docs, user manuals, SOPs, wikis, changelogs, code documentation generation; outdated content detection
**Integrations:** Docs module, Documents module, Slides module
**Autonomous:** Weekly outdated content scan; changelog generation on demand

### Flux — Supply Chain Platform
**Skills:** Supplier risk assessment, purchase order recommendations, stock risk analysis
**Integrations:** Inventory module, Order Mgmt module, WMS module, Delivery module
**Autonomous:** Weekly supplier assessment; stock risk analysis on low inventory triggers

### Hera — HR Platform
**Skills:** Policy Q&A, onboarding plan generation, leave assessment, HR communication drafting
**Integrations:** HR module, Payroll module, Recruitment module, Attendance module
**Autonomous:** Weekly onboarding status check; leave queue processing daily

### Kai — DevOps Platform
**Skills:** Incident root-cause analysis, pipeline health scoring, deployment checklists, infrastructure recommendations
**Integrations:** GitHub/GitLab (via AgentIntegration inbound webhook), PagerDuty, Slack, Factory Ops module
**Autonomous:** Pipeline health check every 30 minutes; daily devops digest
**Inbound webhook:** GitHub push/PR events → `/agents/webhook/<token>/`

### Lead Hunter — B2B Prospecting Platform
**Skills:** ICP fit scoring, outreach sequence generation (5 touches over 21 days), objection responses, channel recommendations
**Integrations:** Leads module, CRM module, Deal Flow module
**Autonomous:** Daily prospect scoring; weekly pipeline digest with conversion metrics

### Luma — Brand & PR Platform
**Skills:** Brand mention sentiment analysis, crisis severity scoring, press release generation, crisis playbook creation
**Integrations:** Website module, Announcements module, Email Marketing module, brand monitoring webhooks
**Autonomous:** Crisis monitoring every 30 minutes; weekly brand health digest
**Inbound webhook:** Mention.com / Google Alerts feed → `/agents/webhook/<token>/`

### MediBook — Healthcare Scheduling Platform
**Skills:** Clinical appointment notes, SMS/email reminders, reschedule suggestions, triage urgency scoring
**Integrations:** Booking module, Care Manager module, Business Calendar module, Twilio (SMS)
**Autonomous:** Appointment reminders every hour; triage urgency flagging

### Merch — eCommerce Platform
**Skills:** Listing optimisation (title, description, pricing), sales analysis, reorder recommendations
**Integrations:** Ecommerce module, Inventory module, Product Catalog module, Store Ops module, Shopify (via AgentIntegration)
**Autonomous:** Daily listing optimisation for unoptimised products; low-stock alerts; reorder checks
**Inbound webhook:** Shopify inventory/order events → `/agents/webhook/<token>/`

### Mira — Customer Success Platform
**Skills:** Health score assessment, churn risk analysis, expansion opportunity detection, email drafting (6 types)
**Integrations:** CRM module, Invoicing module, Reports module
**Autonomous:** Health score refresh daily; churn risk escalation alerts; weekly digest

### Nexus — L&D Platform
**Skills:** Course module generation with quizzes, personalised learning path creation, assessment generation
**Integrations:** LMS module, Training module, Assessments module, HR module
**Autonomous:** Weekly learner progress report; course completion follow-ups

### Nova — Data Science Platform
**Skills:** Natural language to SQL (SELECT-only safety enforced), result analysis, anomaly detection, visualisation suggestions
**Integrations:** Data Studio module, Reports module, AI Analytics module, Dashboard Pro module
**Autonomous:** Pending NL query processing every hour; weekly data digest with anomaly highlights

### Oracle — SEO Platform
**Skills:** Full site SEO audit (7 issue types), keyword research, meta tag optimisation, competitor backlink analysis
**Integrations:** Website module, Email Marketing module, Google Search Console (via AgentIntegration)
**Autonomous:** Weekly SEO audit; keyword gap analysis; meta optimisation queue
**Inbound webhook:** Google Search Console crawl alerts → `/agents/webhook/<token>/`

### Payload — Procurement Platform
**Skills:** RFQ evaluation with vendor ranking, vendor risk assessment, RFQ document drafting
**Integrations:** Inventory module, Order Mgmt module, Contracts module
**Autonomous:** Weekly vendor assessment review; RFQ processing queue daily

### Pulse — Market Intelligence Platform
**Skills:** Market report generation, trend analysis with web search, competitor positioning, battle card creation
**Integrations:** Reports module, Data Studio module, AI Analytics module
**Autonomous:** Weekly market scan with live web intelligence; competitor tracking

### Realt — Real Estate Platform
**Skills:** Property listing copy generation, lead qualification scoring (hot/warm/cold), property-to-buyer matching
**Integrations:** Property Listings module, RE Marketing module, RE Client Portal module, Booking module
**Autonomous:** Stale lead follow-up daily; weekly listing quality digest

### Reporting Bot — Analytics Platform
**Skills:** Narrative report generation, KPI anomaly highlighting, executive summary drafting (3 sentences)
**Integrations:** Reports module, Dashboard Pro module, Data Studio module
**Autonomous:** Scheduled report generation daily; delivery to stakeholders; weekly executive PDF

### Sage — Legal Review Platform
**Skills:** Contract risk scoring (0-100), clause-by-clause plain-English explanation, contract comparison against market standard, counsel requirement flagging
**Integrations:** Contracts module, Documents module
**Autonomous:** Auto-review queued documents every 4 hours; high-risk document alerts daily
**Inbound webhook:** DocuSign/HelloSign signing complete → `/agents/webhook/<token>/`

### Scout — Competitor Intelligence Platform
**Skills:** Competitor change impact analysis, full competitor profile generation, pricing response strategy, weekly intel summaries
**Integrations:** Reports module, AI Analytics module, Data Studio module, competitor RSS/web monitoring
**Autonomous:** Unprocessed change analysis daily; weekly intel digest with strategic recommendations

### Scribe — Meeting Intelligence Platform
**Skills:** Meeting transcript processing, executive summary generation, action item extraction with assignees, sentiment analysis
**Integrations:** Recall.ai (bot management), Video Meet module, Business Calendar module, Task Board module, Docs module
**Autonomous:** Background transcript processing triggered by Recall.ai webhook on meeting end
**Inbound webhook:** Recall.ai transcript delivery → `/agents/webhook/<token>/`

### Shield — IT Helpdesk Platform
**Skills:** Ticket resolution with AI confidence scoring, SLA assessment, KB article generation from resolutions
**Integrations:** Team Chat module, IT monitoring systems (via AgentIntegration inbound webhook)
**Autonomous:** Auto-resolve tickets every 4 hours; SLA monitoring every 30 minutes; KB article creation
**Inbound webhook:** IT monitoring alerts → `/agents/webhook/<token>/`

### Sylvia (Pitch Presenter) — AI Video Pitch Platform
**Skills:** Pitch script generation tailored to audience (investors, enterprise B2B, etc.), slide talking point generation, HeyGen/D-ID video render orchestration
**Integrations:** HeyGen/D-ID Video API, Slides module, Documents module
**Autonomous:** Video generation pipeline triggered per pitch; render status via inbound webhook
**Inbound webhook:** HeyGen render complete → `/agents/webhook/<token>/`

### Tempo — Events Platform
**Skills:** Full event plan generation (checklist, run-of-show, budget, vendors, contingency), attendee messages (5 types), post-event ROI analysis
**Integrations:** Booking module, Business Calendar module, Announcements module
**Autonomous:** Event plans generated for planning/confirmed events daily; 2-week and day-before reminders; RSVP follow-up

### Voice Receptionist — Telephony AI Platform
**Skills:** Real-time call intent detection, multi-turn intake conversations, spam scoring, appointment confirmation drafting, weekly call analytics
**Integrations:** Twilio (inbound calls), Google Voice, Google Calendar, Booking module, CRM module
**Autonomous:** 2-hour appointment reminders every 15 minutes; 24-hour reminders hourly; daily call digest; spam cleanup weekly
**Inbound webhook:** Twilio call/SMS events → `/agents/webhook/<token>/`

---

## Module → Agent Integration Matrix

Which agent naturally augments which module:

| Module | Primary Agent(s) | What the agent does |
|--------|-----------------|---------------------|
| `crm` | Crux, Mira, Lead Hunter | Score contacts, detect churn risk, generate follow-up sequences |
| `leads` | Lead Hunter, Crux | Score ICP fit, build outreach sequences, qualify prospects |
| `invoicing` | Mira, Cash | Flag overdue invoices, detect payment anomalies |
| `contracts` | Sage | Auto-review documents, flag high-risk clauses |
| `hr` | Hera, Nexus, Cash | Generate onboarding plans, assess leave, process payroll |
| `payroll` | Cash | Monthly payroll narratives, anomaly detection |
| `recruitment` | Hera | Draft job descriptions, screen candidate communications |
| `attendance` | Hera | Flag absence patterns, auto-alerts |
| `training` | Nexus, Hera | Generate courses, build learning paths, create assessments |
| `lms` | Nexus | Course delivery, completion tracking, progress reports |
| `accounting` | Cash, Reporting Bot | Financial summaries, anomaly flagging |
| `inventory` | Flux, Merch, Payload | Stock risk analysis, reorder recommendations, listing optimisation |
| `order_mgmt` | Flux, Payload | PO recommendations, supplier assessments |
| `ecommerce` | Merch | Listing optimisation, pricing suggestions, sales analysis |
| `product_catalog` | Merch | Product description generation, tag optimisation |
| `booking` | MediBook, Tempo, Concierge, Voice Receptionist, Realt, Chloe | Appointment reminders, event planning, scheduling |
| `pos` | Merch, Reporting Bot | Sales analysis, daily reporting |
| `website` | Oracle, Luma, Content Architect | SEO audits, brand monitoring, content generation |
| `email_marketing` | Content Architect, Oracle, Babel, Luma | Campaign strategy, translation, meta copy |
| `announcements` | Luma, Tempo, Babel | Press releases, event announcements, translations |
| `docs` | Dox, Scribe | Documentation generation, meeting notes |
| `documents` | Sage, Dox, Babel | Legal review, technical writing, translation |
| `slides` | Sylvia, Dox | Video pitch scripts, presentation documentation |
| `video_meet` | Scribe, Chloe | Meeting notetaking, live video support |
| `business_calendar` | Atlas, Tempo, MediBook, Concierge | Briefings, event reminders, appointment scheduling |
| `task_board` | Atlas, Scribe | Task extraction, priority scoring, action item assignment |
| `team_chat` | Aria, Shield | Ticket intake, IT helpdesk support |
| `reports` | Nova, Reporting Bot, Pulse, Scout, Clarity | KPI reports, market intelligence, competitor tracking |
| `data_studio` | Nova, Pulse, Scout, Reporting Bot | NL-to-SQL, trend analysis, competitor analysis |
| `ai_analytics` | Nova, Pulse, Scout | Anomaly detection, market scanning |
| `dashboard_pro` | Nova, Reporting Bot | Visualisation suggestions, KPI narrative |
| `forms_builder` | Clarity | Survey theme extraction, sentiment analysis |
| `property_listings` | Realt | Listing copy generation, buyer matching |
| `re_marketing` | Realt | Lead qualification, stale follow-up |
| `pms` | Tempo, MediBook | Room booking coordination, guest communications |
| `care_manager` | MediBook | Clinical notes, triage urgency assessment |
| `factory_ops` | Kai | Pipeline health, incident analysis |
| `maintenance` | Kai, Flux | Predictive maintenance alerts, supplier parts orders |

---

## External Deployment Options

### 1. REST API — Plug Into Any System

Any agent's API is available at:
```
https://yourdomain.com/hub/<business-slug>/agents/<agent-slug>/<resource>/
```

**Authentication:** Django session or DRF token (header: `Authorization: Token <token>`)

**Example — trigger Aria ticket resolution:**
```bash
curl -X POST https://yourdomain.com/hub/acme-corp/agents/aria/tickets/ \
  -H "Authorization: Token abc123" \
  -H "Content-Type: application/json" \
  -d '{"subject": "Login broken", "description": "Cannot log in since yesterday", "priority": "high"}'
```

### 2. Inbound Webhook — Event-Driven Integration

Register a webhook endpoint for any agent, then point your external system at it.

**Register (Python/Django shell):**
```python
from agents.models import AgentInstance, AgentWebhookEndpoint
import secrets

instance = AgentInstance.objects.get(catalog__slug='merch', business__slug='acme-corp')
endpoint = AgentWebhookEndpoint.objects.create(
    instance=instance,
    source='shopify',
    url_token=secrets.token_urlsafe(32),
    secret='your-hmac-secret',
)
print(f"Webhook URL: /agents/webhook/{endpoint.url_token}/")
```

**Send event (from Shopify or any system):**
```bash
curl -X POST https://yourdomain.com/agents/webhook/<token>/ \
  -H "X-Hub-Signature-256: sha256=<hmac>" \
  -H "Content-Type: application/json" \
  -d '{"product_id": "123", "inventory_quantity": 2}'
```

The receiver verifies the HMAC and routes to `agents/merch/webhooks.py:handle_event()`.

### 3. External Integrations — AgentIntegration Model

Store encrypted credentials for any platform:
```python
from agents.models import AgentInstance, AgentIntegration

AgentIntegration.objects.create(
    instance=instance,
    platform='slack',
    label='Acme Corp #alerts',
    credential='https://hooks.slack.com/services/...',  # auto-encrypted
    config={'channel': '#ai-alerts'},
    status='connected',
)
```

The agent's `SlackAdapter` or `EmailAdapter` reads these credentials at runtime.

### 4. Standalone Celery Mode

Any agent can run with no module subscriptions. Set `AgentInstance.status = 'idle'` with the relevant `AgentIntegration` records and the Celery Beat tasks will fire on schedule, pulling data from external systems.

---

## Human-in-the-Loop Flow

When any agent is uncertain, it stops and waits for human approval:

```
Agent raises PermissionRequired(context, option_a, option_b)
          ↓
AgentPermissionRequest created (instance, context, options)
          ↓
Email + Slack notification sent to business owner
AgentInstance.status → 'waiting' (agent stops acting)
          ↓
Owner visits: GET /agents/permission/<id>/respond/
          ↓
Owner submits: POST /agents/permission/<id>/respond/ {"decision": "approved"}
          ↓
resume_after_permission Celery task fires:
  - Logs decision to AgentLog
  - Calls agent's handle_permission_resume() if defined
  - Resets AgentInstance.status → 'idle'
  - Next Celery Beat cycle: agent resumes
```

Full audit trail: every action, decision, model used, and token count stored in `AgentLog`.

---

## Adding a New Agent

See [`docs/agents/AGENT_TEMPLATE.md`](../agents/AGENT_TEMPLATE.md) for the complete file-by-file implementation pattern.

**Checklist:**
- [ ] `agents/<name>/` directory with all standard files
- [ ] FK uses `'bredbound.BusinessInstance'` not `'hub.BusinessInstance'`
- [ ] `apps.py` has `ready()` wiring signals
- [ ] `engine.py` raises `PermissionRequired` for low-confidence decisions
- [ ] `tasks.py` loads `AgentInstance` per-business, catches `PermissionRequired`
- [ ] Added to `INSTALLED_APPS`, `CELERY_BEAT_SCHEDULE`, and `bengalbound_core/urls.py`
- [ ] Seed entry in `agents/management/commands/seed_agents.py`
- [ ] Migration created and applied
- [ ] Agent slug added to `_SKIP_SEGMENTS` in `hub/middleware.py` if needed
