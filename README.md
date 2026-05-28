# BengalBound HUB — Backend

**BengalBound HUB** is a Django 4.2 LTS multi-tenant SaaS business operating system. It provides 80+ pluggable business modules, a 30-agent AI Employee Marketplace, and subdomain-routed admin surfaces — all backed by LiteLLM for AI model routing.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 4.2 LTS |
| Auth | django-allauth (email + Google / Facebook / GitHub OAuth) |
| AI | LiteLLM proxy — model-agnostic gateway over any LLM provider |
| Task Queue | Celery + Redis · 85+ scheduled tasks via Celery Beat |
| Database | SQLite (dev) / PostgreSQL (production via `DATABASE_URL`) |
| API | Django REST Framework (DRF) — ViewSets per agent and module |
| Security | django-axes · django-otp (TOTP 2FA) · django-simple-history · django-encrypted-model-fields |
| Telephony | Twilio · Google Voice (Voice Receptionist agent) |

---

## Project Structure

```
bengalbound_core/          # Django project root
  settings/
    base.py                # Shared settings, CELERY_BEAT_SCHEDULE (85+ tasks)
    development.py         # Local dev overrides
    production.py          # Production hardening + PostgreSQL

hub/                       # Core tenant engine (app label: bredbound)
  models.py                # BusinessInstance, ModuleCatalog, TenantModule,
                           # BusinessEmployee, BusinessSubscription, ConnectorSession
  middleware.py            # BusinessAccessMiddleware (IP-lock + slug routing)
  context_processors.py   # Sidebar data injected into all templates
  management/commands/
    seed_modules.py        # python manage.py seed_modules

agents/                    # 30 AI Employee sub-apps
  utils.py                 # agent_chat() — the ONLY LiteLLM call wrapper
  models.py                # AgentCatalog — marketplace registry
  management/commands/
    seed_agents.py         # python manage.py seed_agents
  <name>/                  # One folder per agent — standard structure:
    engine.py              #   AI brain — SYSTEM_PROMPT + domain methods
    tasks.py               #   Autonomous Celery tasks (runs on its own schedule)
    models.py              #   Domain models, FK → 'bredbound.BusinessInstance'
    views.py               #   DRF ViewSets
    serializers.py
    urls.py
    migrations/
  voice_receptionist/      # Extended telephony stack (+ standard engine/tasks)
    ai_engine.py           #   Real-time call NLU processor
    twilio_handler.py      #   Twilio call/SMS lifecycle
    spam_filter.py         #   Caller spam scoring
    calendar_sync.py       #   Google Calendar appointment booking
    notifications.py       #   Post-call Slack/email notifications
    analytics.py           #   Call analytics and reporting
    scheduler.py           #   APScheduler (legacy; Celery tasks added)

modules/                   # 80+ optional business domain apps
  crm/  leads/  invoicing/  contracts/
  hr/  payroll/  recruitment/  attendance/  shift_planning/  training/  expense/
  accounting/  budgeting/  financials/
  inventory/  order_mgmt/  bom/  production/  quality_control/  maintenance/  delivery/
  pos/  ecommerce/  loyalty/  booking/  table_mgmt/
  email_marketing/  announcements/  documents/  website/
  reports/  ai_analytics/  ai_assistant/  dashboard_pro/
  docs/  sheets/  slides/  forms_builder/
  business_mail/  video_meet/  cloud_drive/  business_calendar/
  erp/  mes/  plm/  cadcam/  asset_management/
  workshop/  dms/  dvi/  tms/  wms/
  data_studio/  process_mapper/
  sis/  lms/  assessments/  timetable/  parent_portal/
  property_listings/  deal_flow/  commission/  re_marketing/  re_client_portal/
  omnichannel/  planogram/  product_catalog/  b2b_portal/  store_ops/
  pms/  channel_manager/  rate_manager/  travel_crm/  group_bookings/
  travel_desk/  hospitality_ops/  care_manager/  garden_ops/
  data_collection/  projects/  factory_ops/

serea/                     # Platform AI runtime (NOT an agent)
  tasks.py                 #   Celery Beat: monitor / content / briefing / reports
  logic.py                 #   LiteLLM routing, Facebook/Instagram webhook processing
  platforms/               #   Facebook, Instagram, and channel adapters

accounts/                  # Custom User model (allauth, email-first)
workspace_admin/           # Internal ops — AI workforce management, hub plans
console_admin/             # Customer console — hire agents, billing, projects
public_site/               # Marketing pages, trial flow, affiliate landing
community_forum/           # Community forum (community.* subdomain)
booking_calendar/          # Appointment model for public-site consult flow
core/                      # Shared abstract models (BaseModel with timestamps)
```

---

## Quick Start (Local Development)

### 1. Clone and set up virtualenv
```bash
git clone -b dev https://github.com/Adre-melech/BengalBound.git
cd BengalBound
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — SECRET_KEY and LITELLM_BASE_URL are required to use AI features
```

Generate a secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Run migrations and seed
```bash
python manage.py migrate
python manage.py seed_modules        # Populates ModuleCatalog (80+ modules)
python manage.py seed_agents         # Populates AgentCatalog (30 AI agents)
python manage.py createsuperuser
```

### 4. Start the dev server
```bash
python manage.py runserver 0.0.0.0:1234
```

> **Port 1234 is required.** `CSRF_TRUSTED_ORIGINS` is configured for port 1234.

### 5. Optional: subdomain surfaces

Add to your OS hosts file (`/etc/hosts` on macOS/Linux, `C:\Windows\System32\drivers\etc\hosts` on Windows):

```
127.0.0.1  workspace.localhost
127.0.0.1  console.localhost
127.0.0.1  community.localhost
```

| URL | Surface |
|-----|---------|
| `http://localhost:1234/` | Public site + Hub |
| `http://workspace.localhost:1234/` | Internal workspace admin |
| `http://console.localhost:1234/` | Customer console |
| `http://community.localhost:1234/` | Community forum |

---

## AI Architecture

### LiteLLM — Model Gateway

All AI calls in this project go through one function: `agents/utils.py:agent_chat()`. It posts to the LiteLLM proxy at `LITELLM_BASE_URL` and returns the model's response as a string. No agent or module calls OpenAI, Groq, or any provider directly.

```python
# The ONLY way to call AI — anywhere in the codebase
from agents.utils import agent_chat

response = agent_chat(messages=[...], model="neural-chat")
```

**Task models** (configurable via environment):

| Task | Default model |
|------|--------------|
| Chat / general | `neural-chat` |
| Moderation | `dolphin-mistral` |
| Content generation | `glm4` |
| Analysis | `qwen2.5-coder` |
| Quick replies | `phi4-mini` |

### Serea — Platform AI Engine (`serea/`)

Serea is the social and webhook layer — it is **not** one of the 30 AI agents. It connects BengalBound to external platforms and runs the shared Celery Beat monitor that keeps the hub healthy.

- **Webhooks**: Facebook Messenger and Instagram (`/serea/webhook/facebook/`, `/serea/webhook/instagram/`)
- **Celery Beat**: monitor (10 min), content (5 min), briefing (daily), reports (daily)
- **Human-in-the-loop**: `POST /serea/permission/<id>/respond/` — clients approve or deny agent permission requests

### 30 AI Agents — Independent Engine Modules

Each of the 30 agents is a fully self-contained Django app with its own AI brain and its own autonomous background tasks. They share nothing with Serea and depend only on `agent_chat()`.

**Every agent follows this pattern:**

| File | Purpose |
|------|---------|
| `engine.py` | `<Name>Engine` class with a rich `SYSTEM_PROMPT` and domain-specific methods. Handles all AI reasoning for the agent's specialty. |
| `tasks.py` | `@shared_task` Celery tasks. Run autonomously on their own schedule — no human trigger required. |
| `models.py` | Domain data models. All tenant-scoped via `FK → 'bredbound.BusinessInstance'`. |
| `views.py` | DRF ViewSets. Clients interact with the agent via REST API. |

**Celery Beat schedule** — 85+ entries in `bengalbound_core/settings/base.py`. Highlights:

| Frequency | Examples |
|-----------|---------|
| Every 15 min | Voice Receptionist 2-hour appointment reminders |
| Every 30 min | Aria SLA breach check, Kai pipeline health, Luma crisis monitor, Shield SLA monitor |
| Every hour | Babel translation queue, MediBook reminders, Nova query processor, VR 24-hour reminders |
| Every 4 hours | Aria auto-resolve tickets, Sage document review, Shield auto-resolve tickets |
| Daily | Atlas morning briefing, Cash payroll anomaly check, Concierge inbox digest, Hera HR digest, Scout competitor updates, Tempo event reminders, and 20+ more |
| Weekly | Babel retry failed jobs, Clarity insight digest, Crux pipeline report, Lead Hunter pipeline digest, Nova data digest, Oracle SEO audit, Pulse market scan, Scout intel digest, VR analytics report, and more |

---

## AI Agent Marketplace

30 specialist AI employees, each assignable to a client business via subscription tier through `workspace_admin.HiredAIEmployee`.

| Category | Agent | Slug | Autonomous Tasks |
|----------|-------|------|-----------------|
| Support | Customer Support | `aria` | Auto-resolve tickets, SLA breach alerts, daily digest |
| Support | Customer Success | `mira` | Health score updates, churn risk alerts, weekly digest |
| Support | Client Concierge | `concierge` | Inbox triage, daily digest |
| Sales | CRM Manager | `crux` | Contact scoring, follow-up sequences, weekly pipeline report |
| Sales | B2B Prospector | `lead-hunter` | Prospect scoring, outreach sequences, weekly pipeline digest |
| Finance | Payroll Processor | `cash` | Monthly payroll reminders, anomaly detection |
| Finance | Procurement Manager | `payload` | Vendor assessments, RFQ processing, weekly review |
| Finance | Automated Reporting | `reporting-bot` | Daily KPI reports, weekly executive summaries |
| HR | HR Agent | `hera` | Onboarding plans, leave assessments, weekly digest |
| HR | L&D Coordinator | `nexus` | Course generation, learning paths, weekly progress report |
| Marketing | Content Strategist | `content-architect` | Content calendar planning, SEO optimisation, weekly audit |
| Marketing | SEO Specialist | `oracle` | Weekly site audit, keyword research, meta optimisation |
| Marketing | Brand & PR | `luma` | Crisis monitoring (30 min), press release generation, weekly brand digest |
| Marketing | Market Research | `pulse` | Weekly market scan, competitor analysis, trend reports |
| Marketing | Content Strategist | `serea-content` | Auto-generate draft pieces, campaign strategy, weekly digest |
| Operations | Executive Assistant | `atlas` | Daily morning briefing, overdue task alerts, weekly summary |
| Operations | Supply Chain Manager | `flux` | Supplier assessments, stock risk analysis, weekly report |
| Operations | Events Manager | `tempo` | Event plans, attendee reminders, RSVP follow-up |
| Analytics | Data Scientist | `nova` | NL-to-SQL query processing, anomaly detection, weekly digest |
| Analytics | Feedback Analyst | `clarity` | Theme extraction, sentiment scoring, weekly insight digest |
| Analytics | Competitor Intel | `scout` | Change analysis, competitor profiling, weekly intel digest |
| Technology | DevOps Engineer | `kai` | Pipeline health (30 min), incident analysis, daily digest |
| Technology | IT Helpdesk | `shield` | Auto-resolve tickets, SLA monitoring (30 min), KB articles |
| Specialist | Legal Reviewer | `sage` | Auto-review queued documents, high-risk alerts |
| Specialist | Technical Writer | `dox` | Page generation, outdated content scan, weekly audit |
| Specialist | Translation | `babel` | Translation queue (1 hr), retry failed jobs |
| Specialist | Real Estate Assistant | `realt` | Listing generation, lead qualification, weekly digest |
| Specialist | Medical Scheduler | `medibook` | Appointment reminders (1 hr), triage urgency |
| Specialist | eCommerce Manager | `merch` | Listing optimisation, reorder checks, low stock alerts |
| Specialist | Phone Receptionist | `voice-receptionist` | Call analysis, reminders (15 min / 1 hr), weekly analytics |

---

## URL Architecture

### Request routing

```
Browser → SubdomainRoutingMiddleware
           ├── workspace.localhost → workspace_urls.py
           ├── console.localhost   → console_urls.py
           ├── community.localhost → community_urls.py
           └── (default)          → urls.py
                                       └── /hub/<slug>/... → BusinessAccessMiddleware
                                                              └── Views + Templates
```

### Hub URL patterns

| Style | Pattern | Example |
|-------|---------|---------|
| **Slug-first** (most modules) | `hub/<slug>/<module>/` | `hub/acme-corp/crm/` |
| **Suite-first** (industrial/specialist) | `hub/<module>/<slug>/` | `hub/erp/acme-corp/` |

Suite-first modules add their prefix to `_SKIP_SEGMENTS` in `hub/middleware.py` so `BusinessAccessMiddleware` does not misread them as business slugs.

---

## Tenant Model

```
BusinessInstance (tenant)
  └── ModuleCatalog → TenantModule (activated modules)
  └── BusinessEmployee (staff, 50+ role types, 9 access levels)
       └── CustomPosition (CEO-defined granular permissions)
  └── BusinessSubscription (freemium / standard / premium / advance)
  └── ConnectorSession (IP-locked remote access tokens)
  └── SyncLog (self-hosted ↔ cloud sync audit)
  └── HiredAIEmployee (workspace_admin) → AgentCatalog (which agents are active)
```

### Subscription tiers

| Tier | Storage | Modules | AI Agents |
|------|---------|---------|-----------|
| Freemium | 5 GB | Basic set | — |
| Standard | 20 GB | Basic + add-ons | Entry tier agents |
| Premium | 50 GB | Full industry set | Standard agents |
| Advance | 100 GB | Fully customisable | All 30 agents |

---

## Management Commands

```bash
# Seed all 80+ modules into ModuleCatalog
python manage.py seed_modules

# Seed AgentCatalog with all 30 AI agents
python manage.py seed_agents

# Standard Django
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic    # Production only
```

---

## Production Deployment

### Required environment variables

```bash
SECRET_KEY=<strong-random-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://user:pass@host:5432/bengalbound
LITELLM_BASE_URL=http://your-litellm-proxy:4000
LITELLM_MASTER_KEY=<your-litellm-key>
FACEBOOK_WEBHOOK_VERIFY_TOKEN=<your-verify-token>
EMAIL_HOST=smtp.yourprovider.com
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
```

### Startup sequence

```bash
export DJANGO_SETTINGS_MODULE=bengalbound_core.settings.production
python manage.py migrate
python manage.py seed_modules
python manage.py seed_agents
python manage.py collectstatic --no-input
gunicorn bengalbound_core.wsgi:application

# In separate processes:
celery -A bengalbound_core worker -l info
celery -A bengalbound_core beat -l info
```

---

## Security

- **django-axes**: account lockout after 5 failed login attempts (1-hour cooldown)
- **django-otp / TOTP**: optional 2FA (QR code provisioning in console)
- **simple-history**: model-level change audit on `BusinessInstance` and `BusinessEmployee`
- **IP-locking**: `BusinessAccessMiddleware` blocks non-allowlisted IPs for `ip_locked` businesses
- **Encrypted fields**: AI credentials stored with Fernet encryption (`django-encrypted-model-fields`)
- **HSTS + secure cookies**: enforced in `production.py`

---

## Known Limitations (Dev Branch)

1. **Template UI only** — views render Django templates. REST API layer (DRF serialisers) exists for agents but not all modules yet. Next.js / Flutter integration needs serialisers added per module.
2. **Suite-first URL inconsistency** — modules mounted as `hub/<module>/<slug>/` do not receive `request.current_business` from middleware; they read the slug from URL kwargs.
3. **NowPayments billing** — console billing uses NowPayments (crypto). Stripe integration is planned (Sprint G).
4. **Test coverage is partial** — `tests/test_serea_logic.py`, `serea/tests.py`, and `agents/voice_receptionist/tests/` exist. Full agent test coverage is Sprint E–H.
5. **`apscheduler` optional** — Voice Receptionist has APScheduler as a legacy dependency. Its jobs are now also registered as Celery tasks. Install `apscheduler` and `django-apscheduler` only if you need the in-process scheduler.

---

## Roadmap

| Sprint | Work | Status |
|--------|------|--------|
| A | AgentCatalog model + seed_agents command | ✅ Done |
| B | Domain models for all 30 agents | ✅ Done |
| C | LiteLLM AI call layer (`agents/utils.py`) | ✅ Done |
| D | DRF API layer + independent engine/tasks per agent | ✅ Done |
| E | Console UI — marketplace, hire flow, agent chat | Planned |
| F | Inspector compliance middleware | Planned |
| G | Stripe billing (alongside NowPayments) | Planned |
| H | Firebase → allauth auth bridge | Planned |

---

## Contributing

1. Branch from `dev`
2. Run `python manage.py migrate && python manage.py seed_modules && python manage.py seed_agents` after pulling
3. Run the server on port 1234 — `python manage.py runserver 0.0.0.0:1234`
4. Open a PR against `dev` — never directly to `main`
5. Read `CLAUDE.md` before editing — critical rules for FK targets, AI calls, and URL middleware
