# BengalBound HUB — Backend

**BengalBound HUB** is the core Django backend that powers the BengalBound business operating system. It provides multi-tenant business management, a 60+ module marketplace, AI automation via Serea, and subdomain-routed admin surfaces.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 4.2 (LTS) |
| Auth | django-allauth (email + Google / Facebook / GitHub OAuth) |
| AI Engine | Serea — LiteLLM proxy over Groq / OpenAI / OpenRouter |
| Task Queue | Celery + Redis (in-memory in dev) |
| Database | SQLite (dev) / PostgreSQL (production) |
| Security | django-axes (brute-force), django-otp (TOTP 2FA), django-simple-history (audit trail) |
| Background | Celery Beat — Serea monitor, content, briefing, and report tasks |

---

## Project Structure

```
bengalbound_core/          # Django project root
  settings/
    base.py                # Shared settings (no secrets)
    development.py         # Local dev overrides
    production.py          # Production hardening + PostgreSQL
  urls.py                  # Root URL table (all hub module includes)
  middleware.py            # SubdomainRoutingMiddleware
  workspace_urls.py        # workspace.localhost routes
  console_urls.py          # console.localhost routes
  community_urls.py        # community.localhost routes

hub/                       # Core tenant engine (app label: bredbound)
  models.py                # BusinessInstance, ModuleCatalog, TenantModule,
                           # BusinessEmployee, CustomPosition, ConnectorSession,
                           # SyncLog, HubPlanConfig, BusinessSubscription,
                           # UserBusinessMembership, StorageIncreaseRequest
  middleware.py            # BusinessAccessMiddleware (IP-lock enforcement)
  context_processors.py   # hub_context — injects sidebar data into templates
  templatetags/hub_tags.py # module_url template tag
  management/commands/
    seed_modules.py        # python manage.py seed_modules

modules/                   # 60+ optional business domain apps
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
  workshop/  dms/  dvi/
  tms/  wms/
  data_studio/  process_mapper/
  sis/  lms/  assessments/  timetable/  parent_portal/
  property_listings/  deal_flow/  commission/  re_marketing/  re_client_portal/
  omnichannel/  planogram/  product_catalog/  b2b_portal/  store_ops/
  pms/  channel_manager/  rate_manager/  travel_crm/  group_bookings/
  travel_desk/  hospitality_ops/
  care_manager/  garden_ops/  data_collection/
  projects/  factory_ops/

accounts/                  # Custom User model (allauth, email-first, roles)
public_site/               # Marketing pages, trial flow, affiliate landing
workspace_admin/           # Internal ops — AI workforce, CMS, hub plans
console_admin/             # Customer console — AI hire, billing, projects
community_forum/           # Community forum (community.* subdomain)
booking_calendar/          # Appointment model for public site consult flow
serea/                     # AI runtime — LiteLLM chat, Facebook/Instagram webhooks
agents/                    # 30 AI agent sub-apps
  management/commands/
    seed_agents.py         # python manage.py seed_agents
  utils.py                 # agent_chat() — single shared LiteLLM call wrapper
  <name>/                  # One folder per agent (aria, atlas, babel … voice_receptionist)
    models.py              # Domain models, FK → 'bredbound.BusinessInstance'
    views.py               # DRF ViewSets
    serializers.py
    urls.py
    migrations/
  voice_receptionist/      # Extended engine (telephony stack)
    ai_engine.py           # Call AI processor
    twilio_handler.py      # Twilio call/SMS handling
    scheduler.py           # In-call task scheduler
    permissions.py         # Human-in-the-loop permission flow
    calendar_sync.py       # Google Calendar integration
    spam_filter.py         # Caller spam scoring
    notifications.py       # Post-call notifications
    google_voice.py        # Google Voice bridge
    analytics.py           # Call analytics
```

---

## Quick Start (Local Development)

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Clone and set up virtualenv
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

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env — only SECRET_KEY is required to start
```

Generate a secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Run migrations and seed
```bash
python manage.py migrate
python manage.py seed_modules        # Populates ModuleCatalog (60+ modules)
python manage.py createsuperuser
```

### 5. Start the dev server
```bash
python manage.py runserver 0.0.0.0:1234
```

> **Port 1234 is required.** `CSRF_TRUSTED_ORIGINS` is configured for port 1234.  
> Access at `http://localhost:1234`

### 6. Optional: subdomain surfaces

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

Two mounting styles coexist in `urls.py`:

| Style | Pattern | Example |
|-------|---------|---------|
| **Slug-first** (most modules) | `hub/<slug>/<module>/` | `hub/acme-corp/crm/` |
| **Suite-first** (industrial/specialist) | `hub/<module>/<slug>/` | `hub/erp/acme-corp/` |

Suite-first modules: `erp`, `mes`, `plm`, `cadcam`, `assets`, `workshop`, `dms`, `dvi`, `tms`, `wms`, `data-studio`, `process-mapper`, `sis`, `lms`, `assessments`, `timetable`, `parent-portal`, `properties`, `deals`, `commission`, `re-marketing`, `re-portal`, `omnichannel`, `planogram`, `product-catalog`, `b2b`, `store-ops`

> `BusinessAccessMiddleware` skips suite-first prefixes so it does not misread them as business slugs. These modules receive the real slug via URL kwargs in their views.

---

## Tenant Model

```
BusinessInstance (tenant)
  └── ModuleCatalog (available modules in the marketplace)
       └── TenantModule (which modules this tenant has activated)
  └── BusinessEmployee (staff with 50+ role types, 9 access levels)
       └── CustomPosition (CEO-defined granular permission sets)
  └── BusinessSubscription (freemium / standard / premium / advance)
  └── ConnectorSession (IP-locked and self-hosted remote access tokens)
  └── SyncLog (self-hosted ↔ cloud sync audit)
  └── UserBusinessMembership (invited non-owner members)
  └── StorageIncreaseRequest (workspace-admin-approved quota bumps)
```

### Subscription tiers

| Tier | Storage | Modules | Installation |
|------|---------|---------|--------------|
| Freemium | 5 GB | Basic set only | Cloud |
| Standard | 20 GB | Basic + per-module add-ons | Cloud (IP-lock add-on) |
| Premium | 50 GB | Full industry set | Cloud + IP-locked |
| Advance | 100 GB | Fully customisable | Cloud + IP-locked + Self-hosted |

---

## AI Engines

### Serea — Shared AI Runtime (`serea/`)

Serea is the central AI backbone. All 28 standard agents call through it via `agents/utils.py:agent_chat()`.

- **Model router**: LiteLLM proxy at `LITELLM_BASE_URL` — abstracts over Groq, OpenAI, and OpenRouter
- **Task models** (configurable via env):

| Task | Default model |
|------|--------------|
| Chat | `neural-chat` |
| Moderation | `dolphin-mistral` |
| Content generation | `glm4` |
| Analysis | `qwen2.5-coder` |
| Quick replies | `phi4-mini` |

- **Webhooks**: Facebook Messenger (`/serea/webhook/facebook/`) and Instagram (`/serea/webhook/instagram/`)
- **Celery Beat schedules**: monitor (10 min), content (5 min), briefing (daily), reports (daily)
- **Human-in-the-loop**: `POST /serea/permission/<id>/respond/` — client approves or denies agent permission requests
- **Shared call wrapper**: `agents/utils.py:agent_chat(messages, model)` — the only way to call AI from any agent

### Voice Receptionist — Telephony Engine (`agents/voice_receptionist/`)

Voice Receptionist is the one agent with its own engine stack, because it handles real-time phone calls rather than request/response API calls.

- **`ai_engine.py`**: Real-time call processor — transcribes speech, generates responses, routes intents
- **`twilio_handler.py`**: Twilio call lifecycle — inbound/outbound calls, SMS, call recording
- **`scheduler.py`**: In-call task queue — schedules follow-ups, callbacks, and post-call summaries
- **`permissions.py`**: Human-in-the-loop — agent pauses and asks staff before taking sensitive actions
- **`calendar_sync.py`**: Google Calendar integration — books appointments directly from a call
- **`spam_filter.py`**: Caller scoring — flags robocalls and known spam numbers before answering
- **`notifications.py`**: Post-call notifications — Slack/email summary to the assigned staff member
- **`google_voice.py`**: Google Voice bridge — forwards calls from GV numbers into the pipeline
- **`analytics.py`**: Call analytics — duration, resolution rate, missed-call tracking
- **Hub URL**: `/hub/<slug>/agents/voice-receptionist/`

---

## Management Commands

```bash
# Seed all 60+ modules into ModuleCatalog
python manage.py seed_modules

# Seed AgentCatalog (30 AI agents)
python manage.py seed_agents

# Standard Django
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic    # Production only
```

---

## Production Deployment

### Environment variables (required in production)

```bash
SECRET_KEY=<strong-random-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://user:pass@host:5432/bengalbound
LITELLM_MASTER_KEY=<your-litellm-key>
FACEBOOK_WEBHOOK_VERIFY_TOKEN=<your-verify-token>
EMAIL_HOST=smtp.yourprovider.com
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
```

### Settings module
```bash
export DJANGO_SETTINGS_MODULE=bengalbound_core.settings.production
python manage.py migrate
python manage.py collectstatic --no-input
gunicorn bengalbound_core.wsgi:application
```

### Production database
Set `DATABASE_URL` in the environment. The production settings file configures PostgreSQL automatically via `dj-database-url`. Without `DATABASE_URL` it falls back to SQLite (not recommended).

---

## Security Notes

- **django-axes**: locks accounts after 5 failed login attempts, 1-hour cooldown
- **django-otp / TOTP**: optional 2FA available via `django-otp` (QR code provisioning)
- **simple-history**: model-level change history on `BusinessInstance` and `BusinessEmployee`
- **IP-locking**: `BusinessAccessMiddleware` blocks non-allowlisted IPs for `ip_locked` businesses; bypassed only with a valid `ConnectorSession` token
- **Encrypted fields**: AI credentials stored with `django-encrypted-model-fields` (Fernet)
- **HSTS + secure cookies**: enforced in `production.py`

---

## Known Limitations (Current Dev Branch)

1. **Template UI only** — all views render Django templates. There is no REST API layer yet. Integration with Next.js or Flutter requires DRF serialisers to be added per resource.
2. **Suite-first URL inconsistency** — modules mounted as `hub/<module>/<slug>/` (ERP, MES, etc.) do not receive `request.current_business` from middleware; they must read slug from URL kwargs instead.
3. **NowPayments billing** — console billing uses NowPayments (crypto). Stripe integration is planned for the next sprint.
4. **Test coverage is partial** — `tests/test_serea_logic.py`, `serea/tests.py`, and `agents/voice_receptionist/tests/` (39 tests) exist. Coverage for the other 28 agents is a next sprint item.
5. **`requirements.txt` is pinned to Django 4.2** — `walkthrough.md` mentions Django 6.x which is an error in that document; the actual installed version is Django 4.2 (LTS).

---

## AI Agent Marketplace

30 specialist AI employees, each a Django sub-app under `agents/` with domain models, DRF ViewSets, and LiteLLM-routed AI calls via `agents/utils.py:agent_chat()`.

| Category | Agents |
|----------|--------|
| Support | Aria (Customer Support), Mira (Customer Success), Concierge |
| Sales & CRM | Crux (CRM Manager), Lead Hunter (B2B Prospector) |
| Finance | Cash (Payroll), Payload (Procurement), Reporting Bot |
| HR | Hera (HR Agent), Nexus (L&D) |
| Marketing | Content Architect, Oracle (SEO), Luma (Brand & PR), Pulse (Market Research), Serea Content |
| Operations | Atlas (Executive Assistant), Flux (Supply Chain), Tempo (Events) |
| Analytics | Nova (Data Scientist), Clarity (Feedback), Scout (Competitor Intel) |
| Technology | Kai (DevOps), Shield (IT Helpdesk) |
| Specialist | Sage (Legal), Dox (Technical Writer), Babel (Translation), Realt (Real Estate), MediBook, Merch, Voice Receptionist |

```bash
python manage.py seed_agents    # Seeds AgentCatalog with all 30 agents
```

See [docs/AGENT_TEMPLATE.md](docs/AGENT_TEMPLATE.md) for the implementation pattern.
See [walkthrough.md](walkthrough.md) for the full sprint plan.

---

## Roadmap

| Sprint | Work | Status |
|--------|------|--------|
| A | AgentCatalog model + seed_agents command | ✅ Done |
| B | Domain models for all 30 agents | ✅ Done |
| C | LiteLLM AI call layer (`agents/utils.py`) | ✅ Done |
| D | DRF API layer per agent | ✅ Done |
| E | Console UI — marketplace, hire flow, chat | Planned |
| F | Inspector compliance middleware | Planned |
| G | Stripe billing (alongside NowPayments) | Planned |
| H | Firebase → allauth auth bridge | Planned |

---

## Contributing

1. Branch from `dev`
2. Run `python manage.py migrate && python manage.py seed_modules` after pulling
3. Run the server on port 1234 (`python manage.py runserver 0.0.0.0:1234`)
4. Open a PR against `dev` — never directly to `main`
5. Read `CLAUDE.md` before editing — critical rules for FK targets and AI calls
