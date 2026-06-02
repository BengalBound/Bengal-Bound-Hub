<div align="center">
  <h1>BengalBound HUB — Backend Engine</h1>
  <p><strong>The Next-Generation AI-as-Employee (AIaaE) SaaS Platform</strong></p>
  <p>83 Business Modules · 33 Autonomous AI Agents · Built on Django 4.2 LTS</p>
</div>

---

## What Is BengalBound HUB?

BengalBound HUB is an enterprise-grade multi-tenant SaaS operating system. Businesses subscribe to **modules** — functional apps (CRM, payroll, ecommerce, etc.) — and **AI Agents** — autonomous AI employees who work inside those modules, enriching data, automating decisions, and surfacing intelligence without human prompting.

Each AI Agent is a **self-contained mini-platform**: it has its own data models, REST API, Celery tasks running on its own schedule, inbound webhooks, encrypted external integrations, human-in-the-loop approval flow, long-term memory, and Django admin. Agents are not plugins on top of a shared AI runtime — they are independent engines connected by a single LiteLLM gateway.

Agents can also be deployed standalone or integrated into any third-party system via REST API or inbound webhook — no module subscription required.

---

## Core Tech Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | Django 4.2 LTS |
| **Auth** | `django-allauth` — email + Google / Facebook / GitHub OAuth |
| **AI Gateway** | LiteLLM Proxy — model-agnostic routing (Gemini, OpenAI, Groq, OpenRouter) |
| **Agent Toolkit** | Universal Agent Toolkit — `search_web`, `scrape_website`, `call_api` (robots.txt-compliant, GDPR PII-stripped) |
| **Task Queue** | Celery + Redis — 90+ independent scheduled tasks |
| **Database** | SQLite (dev) / PostgreSQL (production) |
| **API** | Django REST Framework — ViewSets per agent and module |
| **Security** | `django-axes`, `django-otp` (TOTP 2FA), `django-simple-history`, `django-encrypted-model-fields` |
| **Telephony** | Twilio + Google Voice (Voice Receptionist) |
| **Video** | HeyGen / D-ID WebRTC (Video Concierge, Pitch Presenter) |
| **Meeting AI** | Recall.ai (Scribe) |

---

## The 33 AI Agents

Every agent is a **mini-platform** with this architecture:

```
agents/<name>/
  engine.py       ← AI brain: SYSTEM_PROMPT + domain methods + PermissionRequired flow
  tasks.py        ← Autonomous Celery tasks on independent schedules
  signals.py      ← Auto-provisions AgentInstance when a business hires the agent
  admin.py        ← Django admin for domain models + AgentLog + permission requests
  webhooks.py     ← Inbound webhook handler (external systems push events here)
  models.py       ← Domain data models (FK → bredbound.BusinessInstance)
  views.py        ← DRF ViewSets (REST API)
  serializers.py
  urls.py
  migrations/
```

### Support & Client Experience

| Agent | Slug | Primary Modules | Autonomous Tasks |
|-------|------|----------------|-----------------|
| **Aria** — Customer Support | `aria` | CRM, Team Chat, Announcements | Auto-resolve tickets (4hr), SLA breach alerts (30min), daily digest |
| **Mira** — Customer Success | `mira` | CRM, Invoicing, Reports | Health score refresh, churn risk alerts, weekly digest |
| **Concierge** — Client Concierge | `concierge` | Booking, Business Calendar, CRM | Daily inbox triage, meeting scheduling |
| **Voice Receptionist** — Phone AI | `voice-receptionist` | Booking, CRM, Business Calendar | 2hr/24hr appointment reminders, spam cleanup, weekly analytics |
| **Chloe (Video Concierge)** — Live Video AI | `chloe` | Video Meet, Booking, CRM | Daily session digest, WebRTC session management |

### Sales & Revenue

| Agent | Slug | Primary Modules | Autonomous Tasks |
|-------|------|----------------|-----------------|
| **Crux** — CRM Manager | `crux` | CRM, Leads, Deal Flow, Invoicing | Contact scoring, follow-up sequences, weekly pipeline report |
| **Lead Hunter** — B2B Prospector | `lead-hunter` | Leads, CRM, Deal Flow | Prospect scoring, outreach sequences, weekly pipeline digest |

### Finance & Operations

| Agent | Slug | Primary Modules | Autonomous Tasks |
|-------|------|----------------|-----------------|
| **Cash** — Payroll Processor | `cash` | Payroll, HR, Accounting | Monthly payroll reminders (day 25), anomaly detection |
| **Payload** — Procurement Manager | `payload` | Inventory, Order Mgmt, Contracts | Vendor assessments, RFQ processing, weekly review |
| **Flux** — Supply Chain Manager | `flux` | Inventory, WMS, Order Mgmt, Delivery | Supplier assessments, stock risk analysis, weekly report |
| **Reporting Bot** — Automated Reporting | `reporting-bot` | Reports, Dashboard Pro, Data Studio | Daily KPI generation, weekly executive PDF summaries |

### HR & People

| Agent | Slug | Primary Modules | Autonomous Tasks |
|-------|------|----------------|-----------------|
| **Hera** — HR Agent | `hera` | HR, Payroll, Recruitment, Attendance, Training | Onboarding plans, leave assessments, weekly digest |
| **Nexus** — L&D Coordinator | `nexus` | LMS, Training, Assessments, HR | Course generation, learning paths, weekly progress report |

### Marketing & Content

| Agent | Slug | Primary Modules | Autonomous Tasks |
|-------|------|----------------|-----------------|
| **Content Architect** | `content-architect` | Website, Email Marketing, Slides | Content calendar planning, SEO optimisation, weekly audit |
| **Content Strategist (Serea)** | `serea-content` | Website, Email Marketing, Announcements | Auto-generate drafts, campaign strategy, weekly digest |
| **Oracle** — SEO Specialist | `oracle` | Website, Email Marketing | Weekly site audit, keyword research, meta optimisation |
| **Luma** — Brand & PR | `luma` | Website, Email Marketing, Announcements | Crisis monitoring (30min), press releases, weekly brand digest |
| **Pulse** — Market Research | `pulse` | Reports, Data Studio, AI Analytics | Weekly market scan, competitor analysis, trend reports |
| **Sylvia (Pitch Presenter)** — AI Video Pitch | `sylvia` | Slides, Documents | AI script generation → HeyGen video render pipeline |

### Analytics & Intelligence

| Agent | Slug | Primary Modules | Autonomous Tasks |
|-------|------|----------------|-----------------|
| **Nova** — Data Scientist | `nova` | Data Studio, Reports, AI Analytics, Dashboard Pro | NL-to-SQL query processing, anomaly detection, weekly digest |
| **Clarity** — Feedback Analyst | `clarity` | Forms Builder, Data Collection, Reports | Theme extraction, sentiment scoring, weekly insight digest |
| **Scout** — Competitor Intel | `scout` | Reports, AI Analytics, Data Studio | Change analysis, competitor profiling, weekly intel digest |
| **Scribe** — AI Meeting Notetaker | `scribe` | Video Meet, Business Calendar, Task Board, Docs | Process Recall.ai transcripts → summary + action items |

### Technology & IT

| Agent | Slug | Primary Modules | Autonomous Tasks |
|-------|------|----------------|-----------------|
| **Kai** — DevOps Engineer | `kai` | Factory Ops, Maintenance | Pipeline health (30min), incident analysis, daily digest |
| **Shield** — IT Helpdesk | `shield` | Team Chat | Auto-resolve tickets, SLA monitoring (30min), KB articles |

### Specialist & Industry

| Agent | Slug | Primary Modules | Autonomous Tasks |
|-------|------|----------------|-----------------|
| **Sage** — Legal Reviewer | `sage` | Contracts, Documents | Auto-review queued docs (4hr), high-risk alerts |
| **Dox** — Technical Writer | `dox` | Docs, Documents, Slides | Page generation, outdated content scan, weekly audit |
| **Babel** — Translation | `babel` | Documents, Announcements, Email Marketing | Translation queue (1hr), retry failed jobs |
| **Atlas** — Executive Assistant | `atlas` | Business Calendar, Task Board, Reports | Daily morning briefing, overdue task alerts, weekly summary |
| **Realt** — Real Estate Assistant | `realt` | Property Listings, RE Marketing, RE Client Portal, Booking | Listing generation, lead qualification, weekly digest |
| **MediBook** — Medical Scheduler | `medibook` | Booking, Care Manager, Business Calendar | Appointment reminders (1hr), triage urgency |
| **Merch** — eCommerce Manager | `merch` | Ecommerce, Inventory, Product Catalog, Store Ops | Listing optimisation, reorder checks, low stock alerts |
| **Tempo** — Events Manager | `tempo` | Booking, Business Calendar, Announcements | Event plans, attendee reminders, RSVP follow-up |

---

## The 83 Business Modules

Modules are pluggable Django apps in `modules/`. Any tenant can activate any module. Agents integrate by querying module models directly via the shared database.

### CRM & Sales
`crm` · `leads` · `invoicing` · `contracts` · `deal_flow` · `commission` · `b2b_portal`

### HR & People Operations
`hr` · `payroll` · `recruitment` · `attendance` · `shift_planning` · `training` · `expense`

### Finance & Accounting
`accounting` · `budgeting` · `financials`

### Supply Chain & Operations
`inventory` · `order_mgmt` · `bom` · `production` · `quality_control` · `maintenance` · `delivery` · `wms` · `tms`

### Commerce & Retail
`pos` · `ecommerce` · `loyalty` · `booking` · `table_mgmt` · `store_ops` · `planogram` · `product_catalog` · `omnichannel`

### Marketing & Communication
`email_marketing` · `announcements` · `website`

### Documents & Collaboration
`docs` · `documents` · `sheets` · `slides` · `forms_builder` · `cloud_drive` · `business_mail` · `video_meet` · `business_calendar` · `task_board` · `team_chat`

### Analytics & Business Intelligence
`reports` · `ai_analytics` · `ai_assistant` · `dashboard_pro` · `data_studio` · `data_collection` · `process_mapper`

### Manufacturing & Engineering
`erp` · `mes` · `plm` · `cadcam` · `dms` · `dvi` · `factory_ops` · `asset_management` · `workshop`

### Real Estate
`property_listings` · `deal_flow` · `re_marketing` · `re_client_portal`

### Hospitality & Travel
`pms` · `channel_manager` · `rate_manager` · `travel_crm` · `group_bookings` · `travel_desk` · `hospitality_ops`

### Education
`sis` · `lms` · `assessments` · `timetable` · `parent_portal`

### Healthcare & Field Services
`care_manager` · `garden_ops` · `projects`

---

## Quality Assurance & Dynamic Testing

BengalBound HUB maintains **100% baseline test coverage** across all 83 modules and 33 agents. 

Rather than maintaining fragile manual boilerplates, the test suite is powered by a **Dynamic Scaffolding Engine** (`scripts/generate_tests_for_all.py`). When run, it recursively traverses every installed app and module, dynamically parses the Data Models, and automatically generates robust test cases that assert ORM validity and instantiation.

### Running the Suite

```bash
# Generate/Update tests for any newly added modules
python scripts/generate_tests_for_all.py

# Run the full suite (typically executes 740+ tests in <3 seconds)
python manage.py test
```

---

## Agent Platform Architecture

### Human-in-the-Loop Permission Flow

When an agent is uncertain (confidence < threshold), it pauses and requests human approval rather than acting autonomously:

```
Agent task runs → low confidence → raises PermissionRequired
  → creates AgentPermissionRequest
  → sends email + Slack to business owner
  → sets AgentInstance.status = 'waiting'

Owner visits /agents/permission/<id>/respond/
  → approves or denies
  → resume_after_permission Celery task fires
  → logs decision to AgentLog
  → resets instance to 'idle'
  → next beat cycle re-evaluates
```

### Shared Foundation Models (`agents/models.py`)

| Model | Purpose |
|-------|---------|
| `AgentCatalog` | Marketplace registry — 33 agent definitions |
| `AgentInstance` | Live running agent per business (status, token budget, config) |
| `AgentLog` | Audit trail — every action, outcome, model used, token count |
| `AgentPermissionRequest` | Human approval request — context, options, decision, who decided |
| `AgentMemory` | Long-term context persisting across task runs |
| `AgentIntegration` | Encrypted external credentials (Slack, GitHub, Shopify, etc.) |
| `AgentWebhookEndpoint` | Inbound webhook registration — `/agents/webhook/<token>/` |

### Platform Adapters (`agents/platform/`)

| Adapter | Used by |
|---------|---------|
| `EmailAdapter` | All agents — permission requests, alerts |
| `SlackAdapter` | All agents — channel notifications, crisis alerts |
| `WebhookReceiver` | Universal inbound — HMAC verification + event dispatch |

### Universal Agent Toolkit (`agents/toolkit.py`)

All 33 agents have native autonomous internet capabilities, legally compliant with EU AI Act, GDPR, and US CFAA:

- **`search_web(query)`** — DuckDuckGo search with PII stripping
- **`scrape_website(url)`** — robots.txt-compliant HTML extraction, transparent `BengalBoundBot/1.0` identity
- **`call_api(url, method, payload)`** — unauthenticated REST API calls

---

## Deploying Agents

### Inside BengalBound Modules (Default)

Agents query module models directly via the shared database. No API calls between agent and module — it's all in-process. Example: Crux reads from `modules.crm.Contact` and writes scored results back.

### Via REST API (Any External System)

Every agent exposes DRF endpoints at:
```
POST /hub/<business-slug>/agents/<agent-slug>/<resource>/
GET  /hub/<business-slug>/agents/<agent-slug>/<resource>/<id>/
```
Authenticate with a valid session or token. Send data, receive AI-processed output.

### Via Inbound Webhook (Event-Driven)

Register a webhook endpoint for any agent:
```python
AgentWebhookEndpoint.objects.create(
    instance=agent_instance,
    source='shopify',            # or github, stripe, calendly, etc.
    url_token='<unique-token>',
    secret='<hmac-secret>',
)
```

Then POST events to:
```
POST /agents/webhook/<token>/
X-Hub-Signature-256: sha256=<hmac>
```

The universal receiver verifies the signature and routes to `agents/<name>/webhooks.py:handle_event()`.

### Standalone (No Module Required)

Each agent can run independently. Set `AgentInstance.status = 'idle'` and the Celery Beat tasks will fire on their own schedule, pulling data from wherever they're configured (via `AgentIntegration` credentials).

---

## Quick Start

```bash
git clone -b dev https://github.com/Adre-melech/BengalBound.git
cd BengalBound
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # set SECRET_KEY and LITELLM_BASE_URL
python manage.py migrate
python manage.py seed_modules    # 83 modules
python manage.py seed_agents     # 33 AI agents
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:1234

# Background workers (separate terminals)
celery -A bengalbound_core worker -l info
celery -A bengalbound_core beat -l info
```

> Port **1234** is required — `CSRF_TRUSTED_ORIGINS` is configured for it.

### Subdomain Surfaces

Add to `/etc/hosts` (or `C:\Windows\System32\drivers\etc\hosts`):
```
127.0.0.1  workspace.localhost
127.0.0.1  console.localhost
127.0.0.1  community.localhost
```

| URL | Surface |
|-----|---------|
| `http://localhost:1234/` | Public site + Hub |
| `http://workspace.localhost:1234/` | Internal workspace admin |
| `http://console.localhost:1234/` | Customer console (hire agents, billing) |
| `http://community.localhost:1234/` | Community forum |

---

## Production Deployment

### Public Site & Hub — Unified Cloud Run Deployment

Both the public-facing marketing site and the SaaS backend are served directly by Django on Google Cloud Run.
### Django Backend — Required Environment Variables

```bash
SECRET_KEY=<strong-random-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgres://user:pass@host:5432/bengalbound
LITELLM_BASE_URL=http://your-litellm-proxy:4000
LITELLM_MASTER_KEY=<your-litellm-key>
SITE_URL=https://yourdomain.com
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### Backend Startup

```bash
export DJANGO_SETTINGS_MODULE=bengalbound_core.settings.production
python manage.py migrate
python manage.py seed_modules && python manage.py seed_agents
python manage.py collectstatic --no-input
gunicorn bengalbound_core.wsgi:application
celery -A bengalbound_core worker -l info -c 4
celery -A bengalbound_core beat -l info
```

---

## Subscription Tiers

| Tier | Storage | Modules | AI Agents |
|------|---------|---------|-----------|
| Freemium | 5 GB | Basic set | — |
| Standard | 20 GB | Basic + add-ons | Entry tier agents |
| Premium | 50 GB | Full industry set | Standard agents |
| Advance | 100 GB | Fully customisable | All 33 agents |

Agents are hired per-business via `workspace_admin.HiredAIEmployee → AgentCatalog`. Hiring triggers an auto-provision signal that creates the `AgentInstance` for that business.

---

## Security

- **django-axes** — account lockout after 5 failed logins (1hr cooldown)
- **django-otp / TOTP** — 2FA with QR provisioning in console
- **simple-history** — model audit trail on BusinessInstance and employees
- **IP-locking** — `BusinessAccessMiddleware` blocks non-allowlisted IPs
- **Encrypted fields** — API keys and OAuth tokens stored with Fernet encryption
- **HMAC webhooks** — all inbound webhooks verified with `X-Hub-Signature-256`
- **HSTS + secure cookies** — enforced in `production.py`
- **robots.txt compliance** — agent web toolkit refuses scraping blocked domains

---

## Contributing

1. Branch from `dev`
2. Run `python manage.py migrate && python manage.py seed_modules && python manage.py seed_agents`
3. Dev server: `python manage.py runserver 0.0.0.0:1234`
4. PR against `dev` — never directly to `main`
5. Read `CLAUDE.md` — critical FK, AI call, and URL middleware rules
6. New agents: follow `docs/agents/AGENT_TEMPLATE.md` for the full mini-platform pattern

---

## Key Documentation

| Document | Purpose |
|----------|---------|
| [`CLAUDE.md`](CLAUDE.md) | AI assistant rules for this codebase |

| [`docs/agents/AGENT_TEMPLATE.md`](docs/agents/AGENT_TEMPLATE.md) | Full mini-platform pattern for new agents |
| [`docs/architecture/AGENT_MODULE_INTEGRATION.md`](docs/architecture/AGENT_MODULE_INTEGRATION.md) | Agent ↔ module integration map + external deployment guide |
| [`docs/architecture/SYSTEM_ARCHITECTURE.md`](docs/architecture/SYSTEM_ARCHITECTURE.md) | Full system architecture |
| [`walkthrough.md`](walkthrough.md) | Sprint history and implementation notes |

---

<div align="center">
  <sub>Built by the BengalBound Engineering Team · Django 4.2 LTS · LiteLLM · Celery</sub>
</div>
