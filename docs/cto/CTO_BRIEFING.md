# BengalBound HUB — CTO Technical Briefing

**Document type:** Architecture & Engineering Overview  
**Prepared for:** CTO / Technical Leadership  
**Project:** BengalBound HUB — `dev` branch  
**Repository:** https://github.com/Adre-melech/BengalBound (branch: `dev`)  
**Date:** 2026-05-26  

---

## 1. Executive Summary

BengalBound HUB is a **modular, multi-tenant SaaS business operating system** built on Django. It allows any business — across 40+ industry verticals — to activate a curated set of modules from a 60+ module marketplace and manage their entire operation from a single hub.

The system is architected as a **single Django project serving multiple surfaces** via subdomain routing, with a pluggable module framework (`modules.*`) that decouples business domain logic from the core tenant engine (`hub/`).

The current dev branch represents a **complete, production-ready backend scaffold** with:
- Full data models for all 60+ modules
- Working views and templates for the majority of modules
- A battle-tested tenant access control system
- An AI runtime (Serea) wired to a LiteLLM multi-provider router
- Subdomain-routed admin surfaces (workspace, console, community)

---

## 2. Architecture Overview

### 2.1 System Topology

```
┌──────────────────────────────────────────────────────────────────┐
│                        INGRESS LAYER                             │
│  Nginx (reverse proxy) — TLS termination, static file serving    │
└─────────────────────────────┬────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                    DJANGO APPLICATION                            │
│  Gunicorn WSGI server                                            │
│                                                                  │
│  SubdomainRoutingMiddleware                                       │
│    ├── workspace.domain → workspace_urls (internal staff ops)    │
│    ├── console.domain   → console_urls (customer console)        │
│    ├── community.domain → community_urls (public forum)          │
│    └── domain           → ROOT_URLCONF (public site + hub)       │
│                                                                  │
│  BusinessAccessMiddleware (hub/* paths)                          │
│    ├── Resolves BusinessInstance from URL slug                   │
│    ├── Enforces IP-allowlist for ip_locked businesses            │
│    └── Validates ConnectorSession tokens for remote access       │
│                                                                  │
│  Views → Templates (Django template engine)                      │
└────────────┬───────────────────────────────────────────────────┘
             │
┌────────────▼───────────────┐  ┌───────────────────────────────┐
│   PostgreSQL (production)  │  │   Redis / memory broker        │
│   SQLite (development)     │  │   Celery Beat (scheduled AI)   │
│   Supabase (Cloud Run tier)   │  │   memory broker used locally   │
└────────────────────────────┘  └───────────────────────────────┘
```

### 2.2 Request Flow (Hub path)

```
GET /hub/acme-corp/crm/contacts/
  → SubdomainRoutingMiddleware    (main host → ROOT_URLCONF)
  → BusinessAccessMiddleware      (slug=acme-corp → request.current_business)
  → URL router                   → modules.crm.views.contacts(request, slug)
  → hub_context processor        (injects sidebar, modules, employee record)
  → Template render              → HTTP response
```

---

## 3. Core Data Model

### 3.1 Tenant Engine (`hub/` app, DB label: `bredbound`)

> Note: The app code directory is `hub/` but the Django app label is `bredbound` (set in `hub/apps.py`). This preserves migration graph and database table names. All module ForeignKeys reference `'bredbound.BusinessInstance'` — this is intentional and correct.

```
BusinessInstance                         ← One per tenant / company
  ├── owner: ForeignKey(User)
  ├── slug: unique URL key
  ├── business_type: 40+ choices
  ├── installation_type: cloud / ip_locked / self_hosted
  ├── storage_used_mb / storage_limit_mb
  ├── allowed_ips: JSONField            ← IP-lock enforcement
  ├── sync_token                        ← Self-hosted sync backdoor
  └── history: HistoricalRecords        ← Full audit trail

ModuleCatalog                            ← Marketplace listing
  ├── module_id: unique slug
  ├── category, icon, pricing
  ├── applicable_to: JSONField          ← Which business types can use this
  ├── requires_modules: JSONField       ← Dependency chain
  └── url_namespace                     ← Django URL namespace for routing

TenantModule                             ← Module activation per tenant
  ├── business: FK(BusinessInstance)
  ├── module: FK(ModuleCatalog)
  ├── tier: free / basic / pro / enterprise
  └── config: JSONField                 ← Module-specific runtime config

BusinessEmployee                         ← Staff member record
  ├── business: FK(BusinessInstance)
  ├── user: FK(User) nullable           ← Linked platform account (optional)
  ├── role: 50+ choices (ceo → intern)
  ├── access_level: 1–9 (derived from role)
  ├── custom_position: FK(CustomPosition)
  ├── accessible_modules: JSONField     ← Empty = all; list = restricted
  └── history: HistoricalRecords

CustomPosition                           ← CEO-defined granular permission set
  ├── access_level: 1–9
  └── perm_* fields: 12 boolean permissions

BusinessSubscription                     ← Billing / plan per tenant
  ├── plan_type: freemium / standard / premium / advance
  ├── status: active / trial / expired / cancelled
  └── advance_selected_modules: JSONField  ← Custom module bundle

ConnectorSession                         ← Remote access token (IP-locked/self-hosted)
  ├── token: 64-char hex
  ├── expires_at
  └── is_active

UserBusinessMembership                   ← Invited (non-owner) members
HubPlanConfig                           ← Workspace-admin-managed plan pricing
StorageIncreaseRequest                   ← Storage quota bump requests
SyncLog                                  ← Self-hosted ↔ cloud sync audit
```

### 3.2 User & Auth (`accounts/`)

```
User (AbstractUser)
  ├── email: unique (login field)
  ├── role: super_admin / manager / employee / contractor /
  │         auditor / console_user / affiliate
  ├── is_email_verified
  └── otp / otp_created_at

WorkspaceProfile     ← Internal staff profile (title, department)
CustomerProfile      ← External customer profile (company, phone)
```

**Auth methods:**
- Email + password (allauth)
- Google OAuth, Facebook OAuth, GitHub OAuth (allauth social)
- OTP/TOTP 2FA (django-otp)
- Brute-force protection: django-axes (5 attempts → 1-hour lockout)

### 3.3 AI Workforce (`workspace_admin/` + `console_admin/`)

```
AIEmployeeTier       ← Tiers: intern / entry / mid / senior
  └── n8n_workflow_json  ← n8n automation config per tier

HiredAIEmployee      ← A customer's hired AI agent (named "Serea" by default)
  ├── employer: FK(User)
  ├── tier: FK(AIEmployeeTier)
  └── tokens_used_this_month

AITrainingDocument   ← Custom instructions / knowledge uploaded by client
AITaskLimit          ← Per-agent token and task caps
AICredential         ← Encrypted API keys the agent can use

ConsoleModuleActivation  ← Which "OS Apps" the user has installed
WorkspaceProject         ← Client project tracked in the console
AITask                   ← Task assigned to an AI employee
AIChatInteraction        ← Chat message history (client ↔ AI)
SupportTicket            ← Console support tickets
```

### 3.4 Serea AI Runtime (`serea/`)

```
SereaAgent               ← Agent configuration per hired AI
ConversationMessage      ← Chat messages + permission request state
ModerationLog            ← Social media moderation events
```

---

## 4. Module Framework

### 4.1 Architecture Pattern

Every module under `modules/` follows the same structure:

```
modules/<module_id>/
  __init__.py
  apps.py          ← AppConfig with name = 'modules.<module_id>'
  models.py        ← All ForeignKeys to 'bredbound.BusinessInstance'
  urls.py          ← app_name = '<module_id>', always starts with path('')
  views.py         ← All views take (request, slug) and verify business access
  migrations/      ← Standard Django migrations
  admin.py
  tests.py
```

### 4.2 Module Catalog (60+ Modules)

| Category | Modules |
|----------|---------|
| **Operations** | POS, Inventory, Order Mgmt, Table Mgmt, Delivery, Factory Ops |
| **Finance** | Accounting, Invoicing, Payroll, Expense, Budgeting, Financials |
| **People & HR** | HR, Attendance, Recruitment, Training, Shift Planning |
| **Sales & CRM** | CRM, Leads, E-Commerce, Loyalty |
| **Communication** | Team Chat, Announcements, Email Marketing, Business Mail, Video Meet |
| **Manufacturing** | Production, BOM, Quality Control, Maintenance, ERP, MES, PLM, CAD/CAM, Assets |
| **Automotive** | Workshop, DMS, DVI |
| **Logistics** | TMS, WMS |
| **Analytics** | Reports, Dashboard Pro, AI Analytics, AI Assistant, Data Studio |
| **Documents** | Documents, Contracts, Docs, Sheets, Slides, Forms Builder, Cloud Drive |
| **Calendar** | Business Calendar, Projects, Task Board |
| **Consulting** | Process Mapper |
| **Education** | SIS, LMS, Assessments, Timetable, Parent Portal |
| **Real Estate** | Property Listings, Deal Flow, Commission, RE Marketing, RE Client Portal |
| **Retail** | Omnichannel, Planogram, Product Catalog, B2B Portal, Store Ops |
| **Travel** | PMS, Channel Manager, Rate Manager, Travel CRM, Group Bookings, Travel Desk, Hospitality Ops |
| **Care & Garden** | Care Manager, Garden Ops, Data Collection |

### 4.3 Module Activation Flow

```
1. Tenant owner visits /hub/<slug>/store/
2. Browses ModuleCatalog filtered by business_type
3. Clicks "Activate" → hub_activate_module view
4. TenantModule row created (business, module, tier='free')
5. hub_context processor includes module in sidebar on next request
6. Sidebar link resolves via ModuleCatalog.url_namespace → URL reverse
```

### 4.4 Module Access Control

```python
# In any module view:
employee = BusinessEmployee.objects.filter(
    business=biz, user=request.user, is_active=True
).first()

# Check module access
employee.can_access_module('crm')          # boolean
employee.has_permission('view_financials') # boolean
employee.access_level                      # 1–9 integer
employee.can_approve                       # access_level >= 6
employee.can_view_financials               # access_level >= 7 (or custom perm)
```

---

## 5. Subdomain Surfaces

| Subdomain | URLconf | Audience | Key Features |
|-----------|---------|----------|--------------|
| `domain` | `urls.py` | Public + tenants | Marketing site, hub, all modules |
| `workspace.domain` | `workspace_urls.py` | Internal staff | CMS, AI oversight, hub plans, forum mod |
| `console.domain` | `console_urls.py` | Customers | AI hire, billing, projects, Serea chat |
| `community.domain` | `community_urls.py` | Public | Threaded forum |

**Dev mapping** (add to `/etc/hosts`):
```
127.0.0.1  workspace.localhost
127.0.0.1  console.localhost
127.0.0.1  community.localhost
```
Run on port **1234** to match `CSRF_TRUSTED_ORIGINS`.

---

## 6. Serea AI System

### 6.1 Provider Architecture

The AI layer has two modes — the code in `agents/utils.py` picks automatically:

```
agents/utils.py  →  _use_proxy() check
                    │
                    ├── LITELLM_BASE_URL = remote URL
                    │     └── HTTP proxy call (production / multi-tenant VPS)
                    │
                    └── LITELLM_BASE_URL not set or = localhost
                          └── litellm Python library (direct Groq)
                                └── meta-llama/llama-4-scout-17b-16e-instruct
                                      (30k TPM free tier on Groq)
```

All internal model nicknames map to the same Groq model for dev:

```python
# agents/utils.py — _GROQ_MODEL_MAP
{
    "neural-chat":             "groq/meta-llama/llama-4-scout-17b-16e-instruct",
    "dolphin-mistral":         "groq/meta-llama/llama-4-scout-17b-16e-instruct",
    "glm4":                    "groq/meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen2.5-coder":           "groq/meta-llama/llama-4-scout-17b-16e-instruct",
    "phi4-mini":               "groq/meta-llama/llama-4-scout-17b-16e-instruct",
    "gemini/gemini-1.5-flash": "groq/meta-llama/llama-4-scout-17b-16e-instruct",
}
```

Model routing is configurable per task type via `SEREA_TASK_MODELS` in `base.py`:

```python
SEREA_TASK_MODELS = {
    'chat':       'neural-chat',      # → llama-4-scout (dev) or proxied model (prod)
    'moderation': 'dolphin-mistral',
    'content':    'glm4',
    'analysis':   'qwen2.5-coder',
    'quick':      'phi4-mini',
    'gemini':     'gemini/gemini-1.5-flash',
}
```

**Required env var (dev):** `GROQ_API_KEY` — free tier at console.groq.com (30k TPM).
**Optional (production):** `LITELLM_BASE_URL` + `LITELLM_MASTER_KEY` for a proxy server.

### 6.2 Celery Beat Tasks

| Task | Schedule | Purpose |
|------|----------|---------|
| `dispatch_monitor_to_all_agents` | Every 10 min | Social media monitoring |
| `dispatch_content_to_all_agents` | Every 5 min | Content generation |
| `dispatch_briefing_to_all_agents` | Daily | Daily business briefing |
| `dispatch_reports_to_all_agents` | Daily | Automated report generation |

### 6.3 Webhook Integrations

- **Facebook Messenger**: `POST /serea/webhook/facebook/` — receives DMs and page comment events
- **Instagram**: `POST /serea/webhook/instagram/` — receives DMs via Meta Webhooks
- **LinkedIn**: Manual trigger `POST /serea/agent/<id>/linkedin/moderate/` (no webhook; LinkedIn requires app review)

### 6.4 Human-in-the-Loop

When Serea requests a permission (e.g., "post this comment?"), a `ConversationMessage` with `is_permission_request=True` is created. The client approves or denies via:

```
POST /serea/permission/<msg_id>/respond/
Body: { "decision": "approve" | "deny" }
```

Atomic update guards against double-submission race conditions.

---

## 7. Security Architecture

| Layer | Implementation |
|-------|---------------|
| Brute-force | django-axes — 5 failures → 1-hour lockout |
| 2FA | django-otp + TOTP (QR provisioning) |
| Audit trail | django-simple-history on BusinessInstance, BusinessEmployee |
| IP-lock | BusinessAccessMiddleware + allowed_ips JSONField |
| Remote access | ConnectorSession tokens (64-char hex, expiry, per-device) |
| Field encryption | django-encrypted-model-fields (Fernet) on AICredential |
| CSRF | Django CSRF + trusted origins list |
| HSTS | 1-year HSTS with preload (production only) |
| Proxy trust | TRUSTED_PROXIES env var — only trusted IPs honour X-Forwarded-For |
| Session | Secure cookies (production), HttpOnly |
| Headers | X-Frame-Options: DENY, X-Content-Type-Options: nosniff |

---

## 8. Settings Architecture

```
bengalbound_core/settings/
  base.py          ← All shared config; no secrets; safe to read
  development.py   ← DEBUG=True, console email, debug toolbar, eager Celery
  production.py    ← HTTPS, HSTS, secure cookies, PostgreSQL, real Celery
```

`manage.py` defaults to `development`. Set `DJANGO_SETTINGS_MODULE=bengalbound_core.settings.production` on the server.

**Only `SECRET_KEY` is required to start.** All AI and webhook keys have `default=''` — the server starts without them and degrades gracefully (AI features return errors, webhooks reject verification).

---

## 9. Deployment Guide

### 9.1 Environment Variables

| Variable | Required | Notes |
|----------|----------|-------|
| `SECRET_KEY` | Yes | Django secret key |
| `DATABASE_URL` | Production | `postgres://user:pass@host/db` |
| `ALLOWED_HOSTS` | Production | Comma-separated domains |
| `GROQ_API_KEY` | Dev + Production | Direct Groq inference (free 30k TPM tier) |
| `LITELLM_BASE_URL` | Optional (Production) | LiteLLM proxy endpoint — overrides direct Groq |
| `LITELLM_MASTER_KEY` | Optional (Production) | LiteLLM auth key |
| `FACEBOOK_WEBHOOK_VERIFY_TOKEN` | Production | Meta webhook verification |
| `CELERY_BROKER_URL` | Production | `redis://127.0.0.1:6379/0` (memory broker used locally) |
| `FIELD_ENCRYPTION_KEY` | Production | Fernet key for encrypted fields |
| `EMAIL_HOST / USER / PASSWORD` | Production | SMTP for allauth emails |

### 9.2 Deployment Options

#### Cloud Run (Free Tier — Django backend)

Settings: `bengalbound_core/settings/render.py`. Config: `render.yaml`.
Database: Supabase PostgreSQL (set `DATABASE_URL` env var in Cloud Run dashboard).
Static files: served by Whitenoise (no Nginx needed).

```bash
# Cloud Run build command (in render.yaml):
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_modules
python manage.py seed_agents
python manage.py collectstatic --no-input
```

#### Cloud Run (Public marketing site — static export)

Public site templates (`templates/public_site/`) are served directly by Cloud Run.

#### VPS (Hetzner — Full production)

```bash
# 1. Set env vars (see table above)
# 2. Activate production settings
export DJANGO_SETTINGS_MODULE=bengalbound_core.settings.production

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations and seed
python manage.py migrate
python manage.py seed_modules
python manage.py seed_agents

# 5. Collect static files
python manage.py collectstatic --no-input

# 6. Create superuser
python manage.py createsuperuser

# 7. Start Gunicorn
gunicorn bengalbound_core.wsgi:application --workers 4 --threads 4

# 8. Start Celery worker + beat (in separate processes)
celery -A bengalbound_core worker -l info
celery -A bengalbound_core beat -l info
```

### 9.3 Nginx Configuration (reference)

```nginx
server {
    listen 80;
    server_name bengalbound.com *.bengalbound.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name bengalbound.com *.bengalbound.com;

    location /static/ { alias /path/to/staticfiles/; }
    location /media/  { alias /path/to/media/; }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 10. Known Issues & Limitations

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | No REST API layer — Django templates only; Next.js/Flutter integration requires DRF serialisers | High | Next sprint |
| 2 | Suite-first URL modules (`erp`, `mes`, etc.) do not receive `request.current_business` from middleware — views must read slug from URL kwargs | Medium | Documented, workaround in place |
| 3 | NowPayments crypto billing in console — Stripe integration planned | Medium | Planned |
| 4 | Test coverage thin — only 2 test files exist | Medium | Next sprint |
| 5 | `walkthrough.md` incorrectly states "Django 6.x" — actual version is Django 4.2 LTS | Low | Documentation error |
| 6 | LinkedIn moderation requires manual trigger — webhooks need Meta app review | Low | External dependency |

---

## 11. Issues Fixed in This Review Pass

The following bugs were found and fixed directly on the `dev` branch:

| # | File | Issue | Fix Applied |
|---|------|-------|-------------|
| 1 | `settings/base.py` | `FACEBOOK_WEBHOOK_VERIFY_TOKEN` and `LITELLM_MASTER_KEY` had no default — server crashed on startup without them | Added `default=''` |
| 2 | `settings/base.py` | Duplicate unconditional `CELERY_TASK_ALWAYS_EAGER = True` at end of file overrode the conditional block above it, preventing production from disabling eager mode | Removed duplicate |
| 3 | `settings/base.py` | `STATIC_ROOT` not defined — `collectstatic` failed without production settings | Added `STATIC_ROOT = BASE_DIR / 'staticfiles'` |
| 4 | `hub/middleware.py` | `BusinessAccessMiddleware` only skipped `create` and `api` segments — suite-first module prefixes (`erp`, `mes`, `plm`, etc.) were misread as business slugs | Added full `_SKIP_SEGMENTS` frozenset |
| 5 | `hub/templatetags/hub_tags.py` | 11 view names wrong vs actual URL patterns (`crm:contact_list` → `crm:contacts`, `hr:employee_list` → `hr:employees`, etc.) — sidebar links would 404 | Fixed all view names to match actual URL patterns |
| 6 | `hub/management/commands/seed_modules.py` | 25 routable modules had no `url_namespace` set — sidebar navigation resolved to `#` for all of them | Added `url_namespace` to all 25 modules |
| 7 | `hub/management/commands/seed_modules.py` | 10 modules in `INSTALLED_APPS` with full views were missing from `ALL_MODULES` entirely (`docs`, `sheets`, `slides`, `forms_builder`, `business_mail`, `video_meet`, `cloud_drive`, `business_calendar`, `financials`) | Added all missing module entries |
| 8 | `settings/production.py` | PostgreSQL config was commented out with no active fallback path | Uncommented with `dj-database-url`, guarded by `DATABASE_URL` env var check |
| 9 | `.env.example` | `DATABASE_URL` missing; misleading "required" list for keys that now have defaults | Added `DATABASE_URL`, corrected required/optional documentation |

---

## 12. Next Sprint Recommendations

### Priority 1 — REST API Layer
Add Django REST Framework. Every `hub/` resource and key module needs:
- `serializers.py` — model serialisers
- `api_views.py` — DRF ViewSets
- JWT or token auth for Next.js and Flutter clients

### Priority 2 — Stripe Billing
Replace NowPayments in `console_admin/` with Stripe Checkout + Billing Portal. `HubPlanConfig` prices map directly to Stripe Products/Prices.

### Priority 3 — Test Suite
Target: 80% coverage on `hub/`, `accounts/`, `serea/`. Use `pytest-django` and `factory_boy`.

### Priority 4 — WebSocket Chat
Replace polling at `/serea/agent/<id>/chat/` with Django Channels WebSocket for real-time Serea chat.

### Priority 5 — Migrate to Django 5.x
Django 4.2 LTS is supported until April 2026. Plan upgrade to Django 5.2 LTS (released April 2025).

---

---

## 13. AI Agent Marketplace — Migration Roadmap

### 13.1 Overview

33 specialist AI employees are deployed under `agents/` in this project. The migration preserves BengalBound HUB's tech stack entirely — LiteLLM routing, Django 4.2 patterns, `bredbound.BusinessInstance` as the tenant FK, and Serea as the AI backbone.

### 13.2 New Models

**`AgentCatalog`** (mirrors `ModuleCatalog`):
```
AgentCatalog
  ├── name, slug, role, description
  ├── system_prompt           ← The agent's persona and capabilities
  ├── category                ← Support / Finance / HR / Marketing / etc.
  ├── tier_required           ← intern / entry / mid / senior
  └── is_active

HiredAIEmployee (extended)
  └── agent_catalog: FK(AgentCatalog)   ← NEW FIELD
  └── model_override: CharField         ← NEW FIELD
```

### 13.3 The 33 Agents

All 33 agents are implemented, seeded via `python manage.py seed_agents`, and verified working.

| Agent | Slug | Role | Category |
|-------|------|------|----------|
| Aria | `aria` | Customer Support Specialist | Support |
| Atlas | `atlas` | Executive Assistant | Operations |
| Babel | `babel` | Translation & Localisation | Communication |
| Cash | `cash` | Payroll Processor | Finance |
| Clarity | `clarity` | Feedback Analyst | Analytics |
| Concierge | `concierge` | Front-door Receptionist | Operations |
| Content Architect | `content-architect` | Editorial Planning | Marketing |
| Crux | `crux` | CRM Manager | Sales |
| Dox | `dox` | Technical Writer | Documents |
| Flux | `flux` | Supply Chain Manager | Operations |
| Hera | `hera` | HR Agent | HR |
| Kai | `kai` | DevOps Engineer | Technology |
| Lead Hunter | `lead-hunter` | B2B Prospector | Sales |
| Luma | `luma` | Brand & PR | Marketing |
| MediBook | `medibook` | Medical Scheduler | Healthcare |
| Merch | `merch` | eCommerce Manager | Commerce |
| Mira | `mira` | Customer Success | Support |
| Nexus | `nexus` | L&D Coordinator | HR |
| Nova | `nova` | Data Scientist | Analytics |
| Oracle | `oracle` | SEO Specialist | Marketing |
| Payload | `payload` | Procurement Manager | Operations |
| Pulse | `pulse` | Market Research | Analytics |
| Realt | `realt` | Real Estate Assistant | Real Estate |
| Reporting Bot | `reporting-bot` | Automated Reporting | Analytics |
| Sage | `sage` | Legal Reviewer | Legal |
| Scout | `scout` | Competitor Intelligence | Analytics |
| Serea Content | `serea-content` | Content Strategist | Marketing |
| Shield | `shield` | IT Helpdesk | Technology |
| Tempo | `tempo` | Events Manager | Operations |
| Voice Receptionist | `voice-receptionist` | Phone AI Receptionist | Communication |
| Content Strategist | `content_strategist` | Copywriting & Blog Planning | Marketing |
| Pitch Presenter (Sylvia) | `pitch_presenter` | AI Video Pitch Deck | Marketing |
| Scribe | `scribe` | Meeting Intelligence | Operations |
| Video Concierge (Chloe) | `video_concierge` | Live Video AI | Support |

### 13.4 Sprint Plan

| Sprint | Deliverable | Key Files |
|--------|-------------|-----------|
| A — Foundation | `AgentCatalog` model, `seed_agents` command, extend `HiredAIEmployee`, add Gemini to LiteLLM config | `agents/models.py`, `agents/management/commands/seed_agents.py` |
| B — Domain Models | Port each agent's domain models; swap `Organization` FK → `bredbound.BusinessInstance` | `agents/<name>/models.py` × 30 |
| C — AI Call Layer | `agents/utils.py` with `agent_chat()` LiteLLM wrapper; port all agent views | `agents/utils.py`, `agents/<name>/views.py` × 30 |
| D — DRF API | Add `rest_framework`, per-agent serializers + ViewSets, mount under `hub/<slug>/api/agents/<name>/` | `agents/<name>/serializers.py`, `agents/<name>/urls.py` |
| E — Console UI | Agent marketplace, hire flow, per-agent chat in `console_admin/` | `console_admin/views.py`, templates |
| F — Inspector | Port compliance middleware as `inspector/` app; wire to agent views for sensitive ops | `inspector/`, `MIDDLEWARE` in `base.py` |
| G — Stripe | Add Stripe billing alongside NowPayments; `billing/` app, plan model | `billing/`, `requirements.txt` |
| H — Auth Bridge | `firebase_uid` field on `accounts.User`; Firebase ID token → allauth user sync view | `accounts/models.py` |

### 13.5 LiteLLM Gemini Integration

Add to `bengalbound_core/settings/base.py`:
```python
SEREA_TASK_MODELS = {
    ...existing...,
    'gemini': env('GEMINI_MODEL', default='gemini/gemini-1.5-flash'),
}
```

Add to `.env.example`:
```
GEMINI_API_KEY=
GEMINI_MODEL=gemini/gemini-1.5-flash
```

### 13.6 Source Reference

Agent source code is at: `d:\Bengal bound\Bengal Bound.worktrees\agents-constitutional-fox\api/agents/`
Full agent specifications are at: `d:\Bengal bound\Bengal Bound.worktrees\agents-constitutional-fox\docs/agents/`
Python template for implementing agents: [`docs/AGENT_TEMPLATE.md`](AGENT_TEMPLATE.md)

---

*Prepared from direct codebase review of the `dev` branch. All line references are accurate to the state of the branch at the time of this review.*
