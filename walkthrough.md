# BengalBound HUB — Codebase Walkthrough

This document maps the **BengalBound-HUB** codebase: a **Django 4.2 LTS** multi-surface product that combines a marketing **public site**, internal **workspace** and **console** admin areas, a **community** forum, per-tenant **business hubs**, a large catalog of optional **`modules.*`** domain apps, and an **AI Agent Marketplace** of 30 specialist agents.

---

## Executive summary

- **What you are building**: A modular **SaaS-style business operating system**. Each end customer has a **`BusinessInstance`** (slug, industry type, storage, optional IP lock / self-hosted sync). They activate capabilities from a **`ModuleCatalog`**; active installs are **`TenantModule`** rows. Employees are **`BusinessEmployee`** records with rich roles, optional **`CustomPosition`** for granular permissions, and optional `accessible_modules` restrictions.
- **How users reach it**: One Django project serves multiple "surfaces" via **`SubdomainRoutingMiddleware`** (different root URLconfs). Day-to-day operations for a company live under **`/hub/<business_slug>/…`** (and several suites under **`/hub/<suite-prefix>/<business_slug>/…`**).
- **What makes it large**: Dozens of Django apps under [`modules/`](modules/) — each can carry `models`, `urls`, `views`, `templates`, and migrations. The authoritative list of installed apps is in [`bengalbound_core/settings/base.py`](bengalbound_core/settings/base.py) (`INSTALLED_APPS`).
- **AI layer**: Serea runtime routes all AI via LiteLLM proxy. The **`agents/`** package hosts 30 specialist AI employees — Aria (Support), Crux (CRM), Hera (HR), Cash (Payroll), Serea Content (Marketing), Voice Receptionist, and 24 more — all fully migrated with domain models, DRF ViewSets, and migrations.

---

## Tech stack

| Area | Details |
|------|---------|
| Framework | Django **4.2 LTS** (`bengalbound_core/settings/base.py`); ignore any comments mentioning Django 6.x — those are documentation errors. |
| Auth | **django-allauth** (email login, mandatory email verification) + social providers (Google, Facebook, GitHub). Custom user: **`accounts.User`** (`AUTH_USER_MODEL`). |
| DB | Default **SQLite** at `BASE_DIR / 'db.sqlite3'`. Production overrides via `DATABASE_URL` env var using `dj-database-url`. |
| Config | **`django-environ`** loads `.env` at project root (copy from `.env.example`; not committed). Settings split into `base.py` / `development.py` / `production.py`. |
| Static / media | `STATICFILES_DIRS = BASE_DIR / 'static'`, `STATIC_ROOT = BASE_DIR / 'staticfiles'`, `MEDIA_ROOT` under `media/`. |
| Background work | **Celery** with dev-friendly in-memory / eager defaults. Production uses Redis broker. Beat schedule runs 4 Serea AI tasks. |
| AI ("Serea") | LiteLLM proxy at `LITELLM_BASE_URL`. Env keys: `GROQ_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`. Facebook webhook: `FACEBOOK_WEBHOOK_VERIFY_TOKEN`. All keys are optional in dev (server starts without them). |

### `requirements.txt`

[`requirements.txt`](requirements.txt) is a standard pinned dependency file. Key packages: `Django==4.2.*`, `celery`, `django-allauth`, `django-axes`, `django-otp`, `django-simple-history`, `django-encrypted-model-fields`, `litellm`, `dj-database-url`, `django-environ`.

---

## Repository layout

| Path | Role |
|------|------|
| [`manage.py`](manage.py) | Django entry; defaults to `bengalbound_core.settings.development`. |
| [`bengalbound_core/settings/base.py`](bengalbound_core/settings/base.py) | All shared config — installed apps, middleware, auth, Celery, AI keys. No secrets. |
| [`bengalbound_core/settings/development.py`](bengalbound_core/settings/development.py) | Debug overrides, console email backend, eager Celery. |
| [`bengalbound_core/settings/production.py`](bengalbound_core/settings/production.py) | HTTPS, HSTS, secure cookies, PostgreSQL via DATABASE_URL. |
| [`bengalbound_core/urls.py`](bengalbound_core/urls.py) | Primary URL table: public site, workspace/console paths, **all hub module includes**, Serea, admin. |
| [`bengalbound_core/middleware.py`](bengalbound_core/middleware.py) | **`SubdomainRoutingMiddleware`** — switches `request.urlconf` per hostname. |
| [`bengalbound_core/workspace_urls.py`](bengalbound_core/workspace_urls.py) | Workspace-only routes + Django admin. |
| [`bengalbound_core/console_urls.py`](bengalbound_core/console_urls.py) | Console dashboard, Serea includes, partial hub includes. |
| [`bengalbound_core/community_urls.py`](bengalbound_core/community_urls.py) | Community forum surface. |
| [`hub/`](hub/) | **Hub core app** — app label `bredbound`. Businesses, modules, subscriptions, employees, connector tokens, sync API. |
| [`hub/middleware.py`](hub/middleware.py) | **`BusinessAccessMiddleware`** — resolves `request.current_business` for `/hub/<slug>/…` (see caveat below). |
| [`hub/context_processors.py`](hub/context_processors.py) | `hub_context` — injects hub sidebar data and resolves module landing URLs via `_MODULE_URL_MAP`. |
| [`hub/templatetags/hub_tags.py`](hub/templatetags/hub_tags.py) | Template tag `module_url` — parallel `MODULE_URL_MAP`. Keep in sync with context processor. |
| [`accounts/`](accounts/) | Custom `User`, workspace and customer profiles. |
| [`public_site/`](public_site/) | Marketing site; integrates `booking_calendar.Appointment` for consult/trial flows. |
| [`workspace_admin/`](workspace_admin/) | Internal admin UI, CMS, AI workforce config, hub pricing. |
| [`console_admin/`](console_admin/) | Customer console: AI hiring, billing webhooks, Serea chat entry. |
| [`community_forum/`](community_forum/) | Forum threads for community subdomain. |
| [`booking_calendar/`](booking_calendar/) | Appointment model (used from `public_site`). |
| [`serea/`](serea/) | AI runtime endpoints and Facebook/Instagram webhook. |
| [`agents/`](agents/) | 30 specialist AI employee apps — fully migrated. Each sub-app has `models.py`, `views.py`, `serializers.py`, `urls.py`, `migrations/`. Seeded via `python manage.py seed_agents`. |
| [`modules/`](modules/) | Optional domain Django apps — see catalog below. |
| [`templates/`](templates/) | Global template dir; many hub screens under `templates/hub/`. |

---

## Request routing: subdomains and URLconfs

[`SubdomainRoutingMiddleware`](bengalbound_core/middleware.py) inspects `Host` (without port):

| Host (dev) | `request.urlconf` |
|------------|-------------------|
| `workspace.localhost` | `bengalbound_core.workspace_urls` |
| `console.localhost` | `bengalbound_core.console_urls` |
| `community.localhost` | `bengalbound_core.community_urls` |
| anything else | default **`ROOT_URLCONF`** → [`bengalbound_core/urls.py`](bengalbound_core/urls.py) |

`CSRF_TRUSTED_ORIGINS` includes `http://localhost:1234` and matching subdomain hosts — run the dev server on **port 1234**, or update settings.

### High-level HTTP flow

```
Browser
  └── SubdomainRoutingMiddleware
        ├── workspace.localhost → workspace_urls.py
        ├── console.localhost   → console_urls.py
        ├── community.localhost → community_urls.py
        └── (default)          → urls.py
                                    └── /hub/<slug>/... → BusinessAccessMiddleware
                                                           └── Views + Templates
```

---

## Hub URLs: two mounting styles

[`bengalbound_core/urls.py`](bengalbound_core/urls.py) mixes two patterns:

1. **Business-first** — `hub/<slug:slug>/<segment>/…`  
   Example: `hub/acme-corp/crm/` → CRM under slug `acme-corp`.

2. **Suite-first** — `hub/<segment>/…` (no business slug in the outer include)  
   Example: `hub/mes/<slug:slug>/…` → MES URLs; inner [`modules/mes/urls.py`](modules/mes/urls.py) defines `<slug:slug>/`.

**`BusinessAccessMiddleware` caveat** ([`hub/middleware.py`](hub/middleware.py)): it treats **the first path segment after `hub/`** as the business slug. For `hub/acme-corp/crm/` that is correct. For `hub/mes/acme-corp/` it would read `mes` as the slug — which is wrong. A `_SKIP_SEGMENTS` frozenset in the middleware prevents this by passing through known suite-first prefixes unchanged. Suite-first modules receive the real slug via **URL kwargs** in their views.

Suite-first prefixes: `erp`, `mes`, `plm`, `cadcam`, `assets`, `workshop`, `dms`, `dvi`, `tms`, `wms`, `data-studio`, `process-mapper`, `sis`, `lms`, `assessments`, `timetable`, `parent-portal`, `properties`, `deals`, `commission`, `re-marketing`, `re-portal`, `omnichannel`, `planogram`, `product-catalog`, `b2b`, `store-ops`.

---

## Hub domain model

Defined in [`hub/models.py`](hub/models.py). The app folder is `hub/` but **Django app label is `bredbound`** (set in `hub/apps.py`). All ForeignKeys in every module reference `'bredbound.BusinessInstance'` — this is intentional; changing it would break the migration graph.

```
BusinessInstance                        ← One per tenant / company
  ├── owner: FK(User)
  ├── slug: unique URL key
  ├── business_type: 40+ choices
  ├── installation_type: cloud / ip_locked / self_hosted
  ├── storage_used_mb / storage_limit_mb
  ├── allowed_ips: JSONField            ← IP-lock enforcement
  ├── sync_token                        ← Self-hosted sync token
  └── history: HistoricalRecords        ← Full audit trail

ModuleCatalog                           ← Marketplace entry for each module
  ├── module_id: unique slug
  ├── category, icon, pricing
  ├── applicable_to: JSONField          ← Which business types can activate
  ├── requires_modules: JSONField       ← Dependency chain
  └── url_namespace                     ← Django URL namespace for sidebar routing

TenantModule                            ← Activation of a module for a tenant
  ├── business: FK(BusinessInstance)
  ├── module: FK(ModuleCatalog)
  ├── tier: free / basic / pro / enterprise
  └── config: JSONField

BusinessEmployee                        ← Staff member
  ├── business: FK(BusinessInstance)
  ├── user: FK(User) nullable
  ├── role: 50+ choices
  ├── access_level: 1–9
  ├── custom_position: FK(CustomPosition)
  └── accessible_modules: JSONField     ← Empty = all access

AgentCatalog                           ← (In progress) AI agent marketplace entries
  └── mirrors ModuleCatalog pattern, seeded by `python manage.py seed_agents`
```

Catalog rows are seeded by:
```bash
python manage.py seed_modules     # 60+ business modules
python manage.py seed_agents      # Seeds all 30 AI agents into AgentCatalog
```

**Linking modules in the UI**: `hub_context` builds `hub_active_module_items` using `ModuleCatalog.url_namespace` and `_MODULE_URL_MAP`. If `url_namespace` is blank in the database, the resolved URL is `'#'`. Every routable module in `seed_modules` now carries a `url_namespace` — sidebar navigation is fully functional after seeding.

---

## Primary URL map

`{slug}` = your `BusinessInstance.slug`.

| Prefix | Namespace / area | Notes |
|--------|------------------|-------|
| `/` | `public_site` | Marketing, trial, affiliates |
| `/admin/` | Django admin | |
| `/accounts/` | allauth + `accounts` | |
| `/workspace/` | `workspace_admin` | Main host; workspace subdomain also mounts at `/` |
| `/console/` | `console_admin` | |
| `/community/` | `community_forum` | |
| `/hub/` | `bredbound` | Landing, create, per-slug dashboard, store, employees, settings, connector, subscription |
| `/hub/{slug}/board/` | `task_board`, `team_chat` | Slug-first collaboration |
| `/hub/erp/{slug}/` | `erp` | Suite-first |
| `/hub/mes/{slug}/` | `mes` | Suite-first; includes scanner webhook |
| `/hub/plm/{slug}/` | `plm` | Suite-first |
| `/hub/cadcam/` | `cadcam` | Suite-first |
| `/hub/assets/` | `asset_management` | Suite-first |
| `/hub/workshop/` | `workshop` | Suite-first |
| `/hub/dms/` | `dms` | Suite-first |
| `/hub/dvi/` | `dvi` | Suite-first |
| `/hub/tms/` | `tms` | Suite-first |
| `/hub/wms/` | `wms` | Suite-first |
| `/hub/data-studio/` | `data_studio` | Suite-first |
| `/hub/process-mapper/` | `process_mapper` | Suite-first |
| `/hub/sis/` | `sis` | Suite-first — Education |
| `/hub/lms/` | `lms` | Suite-first |
| `/hub/assessments/` | `assessments` | Suite-first |
| `/hub/timetable/` | `timetable` | Suite-first |
| `/hub/parent-portal/` | `parent_portal` | Suite-first |
| `/hub/properties/` | `property_listings` | Suite-first — Real estate |
| `/hub/deals/` | `deal_flow` | Suite-first |
| `/hub/commission/` | `commission` | Suite-first |
| `/hub/re-marketing/` | `re_marketing` | Suite-first |
| `/hub/re-portal/` | `re_client_portal` | Suite-first |
| `/hub/omnichannel/` | `omnichannel` | Suite-first — Retail |
| `/hub/planogram/` | `planogram` | Suite-first |
| `/hub/product-catalog/` | `product_catalog` | Suite-first |
| `/hub/b2b/` | `b2b_portal` | Suite-first |
| `/hub/store-ops/` | `store_ops` | Suite-first |
| `/hub/{slug}/pms/` | `pms`, `channel_manager`, `rate_manager`, `travel_crm`, `group_bookings`, `travel_desk`, `hospitality_ops` | Slug-first — Travel |
| `/hub/{slug}/care/` | `care_manager`, `garden_ops`, `data_collection` | Slug-first |
| `/f/<form_slug>/` | `forms_builder` public | No business slug |
| `/serea/` | `serea` | Agent chat, logs, Facebook webhook |

`console_urls` additionally mounts `/hub/` (bredbound + board + chat) on the console host.

---

## `modules.*` catalog

All apps are registered in `INSTALLED_APPS`. Each provides `models.py`, `urls.py` (with `app_name` matching URL namespace), `views.py`, and `templates/<app_label>/`. Schema changes live in `migrations/` per app.

### Collaboration
| App | Role |
|-----|------|
| `modules.task_board` | Kanban / tasks per business |
| `modules.team_chat` | Team channels |

### CRM and sales
| App | Role |
|-----|------|
| `modules.crm` | Contacts, deals, activities |
| `modules.leads` | Lead capture and pipeline |
| `modules.invoicing` | Invoices and billing UI |
| `modules.contracts` | Contract records / workflow |

### HR and people
| App | Role |
|-----|------|
| `modules.hr` | Core HR records |
| `modules.payroll` | Payroll |
| `modules.recruitment` | Hiring pipeline |
| `modules.attendance` | Time and attendance |
| `modules.shift_planning` | Rosters / shifts |
| `modules.training` | Training programs |
| `modules.expense` | Expense claims |

### Finance
| App | Role |
|-----|------|
| `modules.accounting` | GL / bookkeeping |
| `modules.budgeting` | Budgets and planning |
| `modules.financials` | Financial statements |

### Operations and supply
| App | Role |
|-----|------|
| `modules.inventory` | Stock, products, lots |
| `modules.order_mgmt` | Sales / purchase orders |
| `modules.bom` | Bill of materials |
| `modules.production` | Manufacturing orders |
| `modules.quality_control` | QC inspections |
| `modules.maintenance` | Asset maintenance |
| `modules.delivery` | Delivery logistics |

### Commerce
| App | Role |
|-----|------|
| `modules.pos` | Point of sale |
| `modules.ecommerce` | Online storefront |
| `modules.loyalty` | Loyalty programs |
| `modules.booking` | Reservations |
| `modules.table_mgmt` | Restaurant / hotel tables |

### Marketing and comms
| App | Role |
|-----|------|
| `modules.email_marketing` | Campaigns |
| `modules.announcements` | Internal announcements |
| `modules.documents` | Document management |
| `modules.website` | Site / page builder hooks |

### Intelligence
| App | Role |
|-----|------|
| `modules.reports` | Reporting dashboards |
| `modules.ai_analytics` | AI-assisted analytics |
| `modules.ai_assistant` | In-product assistant |
| `modules.dashboard_pro` | Advanced dashboarding |

### Creation suite
| App | Role |
|-----|------|
| `modules.docs` | Collaborative documents |
| `modules.sheets` | Spreadsheets |
| `modules.slides` | Presentations |
| `modules.forms_builder` | Form builder + public submit at `/f/<slug>/` |

### Communication and productivity
| App | Role |
|-----|------|
| `modules.business_mail` | Mailbox UI |
| `modules.video_meet` | Meetings |
| `modules.cloud_drive` | File storage UI |
| `modules.business_calendar` | Shared calendars |

### Manufacturing and industrial
| App | Role |
|-----|------|
| `modules.erp` | ERP dashboard, ledger, journals |
| `modules.mes` | Manufacturing execution, work centers |
| `modules.plm` | Product lifecycle |
| `modules.cadcam` | CAD/CAM integration |
| `modules.asset_management` | Industrial assets / tooling |

### Automotive
| App | Role |
|-----|------|
| `modules.workshop` | Workshop / garage |
| `modules.dms` | Dealer management |
| `modules.dvi` | Digital vehicle inspection |

### Logistics
| App | Role |
|-----|------|
| `modules.tms` | Transportation management |
| `modules.wms` | Warehouse management |

### Consulting and analytics
| App | Role |
|-----|------|
| `modules.data_studio` | Datasets / exploration |
| `modules.process_mapper` | Process mapping |

### Education
| App | Role |
|-----|------|
| `modules.sis` | Student information |
| `modules.lms` | Courses / learning |
| `modules.assessments` | Quizzes / tests |
| `modules.timetable` | Scheduling |
| `modules.parent_portal` | Parent / guardian portal |

### Real estate
| App | Role |
|-----|------|
| `modules.property_listings` | Listings |
| `modules.deal_flow` | Transaction pipeline |
| `modules.commission` | Commissions |
| `modules.re_marketing` | RE marketing |
| `modules.re_client_portal` | Client portal |

### Retail and wholesale
| App | Role |
|-----|------|
| `modules.omnichannel` | Omnichannel retail |
| `modules.planogram` | Shelf planning |
| `modules.product_catalog` | PIM-style catalog |
| `modules.b2b_portal` | B2B ordering portal |
| `modules.store_ops` | Store operations |

### Travel and accommodation
| App | Role |
|-----|------|
| `modules.pms` | Property management system |
| `modules.channel_manager` | OTA channel connectivity |
| `modules.rate_manager` | Rates / restrictions |
| `modules.travel_crm` | Travel-specific CRM |
| `modules.group_bookings` | Groups / tours |
| `modules.travel_desk` | Agency desk |
| `modules.hospitality_ops` | Day-to-day hospitality ops |

### Personal care, home, and garden
| App | Role |
|-----|------|
| `modules.care_manager` | Care scheduling / clients |
| `modules.garden_ops` | Garden / field operations |
| `modules.data_collection` | Field data capture |

---

## Other first-party apps

| App | Role |
|-----|------|
| `accounts` | `AbstractUser` subclass, roles, workspace vs customer profiles |
| `public_site` | Marketing site; uses `booking_calendar.Appointment` for consult/trial flows |
| `workspace_admin` | Internal admin UI, CMS, Serea config, hub pricing |
| `console_admin` | Customer console: AI hiring, billing, projects, Serea chat |
| `community_forum` | Forum threads for community subdomain |
| `booking_calendar` | Appointment model (no dedicated URLconf in root; used from `public_site`) |
| `serea` | AI runtime endpoints and Facebook webhook |

---

## Serea AI engine

- **URLs**: `serea/urls.py` — permission responses, chat send/history, moderation logs, `webhook/facebook/`.
- **Console integration**: `console_admin/urls.py` mounts `path('serea/', include('serea.urls'))`.
- **LiteLLM routing**:

```python
SEREA_TASK_MODELS = {
    'chat':       'neural-chat',
    'moderation': 'dolphin-mistral',
    'content':    'glm4',
    'analysis':   'qwen2.5-coder',
    'quick':      'phi4-mini',
}
```

All AI calls go through the LiteLLM proxy (`LITELLM_BASE_URL`). **Never call Groq, OpenAI, or Gemini directly** — always use the proxy.

- **Celery Beat**: monitor (10 min), content (5 min), briefing (daily), reports (daily).
- **Human-in-the-loop**: `POST /serea/permission/<id>/respond/` — approve or deny agent actions.

---

## Local development quick start

```bash
# 1. Create .env
cp .env.example .env
# Edit .env — only SECRET_KEY is required

# 2. Install dependencies
python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # macOS / Linux
pip install -r requirements.txt

# 3. Migrate and seed
python manage.py migrate
python manage.py seed_modules  # Populates ModuleCatalog

# 4. Create superuser
python manage.py createsuperuser

# 5. Run on port 1234 (required for CSRF)
python manage.py runserver 0.0.0.0:1234

# 6. Add to OS hosts file for subdomain testing
# 127.0.0.1  workspace.localhost
# 127.0.0.1  console.localhost
# 127.0.0.1  community.localhost
```

---

## URL namespace verification

- **Django route namespaces** come from `include(..., namespace='…')` in `bengalbound_core/urls.py`. Each `modules.<pkg>.urls` should set matching `app_name`.
- **`seed_modules` `url_namespace`**: All routable modules now carry a `url_namespace` aligned with their Django URL namespace (fixed in review pass). After running `seed_modules`, all sidebar links resolve correctly — no `'#'` placeholders for navigable modules.
- **Landing view names**: `hub/context_processors.py` `_MODULE_URL_MAP` is the authoritative source. `hub/templatetags/hub_tags.py` `MODULE_URL_MAP` is kept in sync (fixed in review pass — previously 14 names were wrong).

---

## Maintenance notes

1. **`_MODULE_URL_MAP` vs `MODULE_URL_MAP`**: Both `hub/context_processors.py` and `hub/templatetags/hub_tags.py` define routing metadata. Keep them aligned — they were out of sync historically but are now reconciled.
2. **`ModuleCatalog.url_namespace`**: Must match Django URL namespaces and `_MODULE_URL_MAP` keys. All navigable modules in `seed_modules` now carry the correct value.
3. **`hub/` folder, `bredbound` label**: The Django app folder is `hub/`. The app label (and DB table prefix) is `bredbound`. Do not rename either.
4. **Suite-first `_SKIP_SEGMENTS`**: If you add a new suite-first module, add its URL prefix to `_SKIP_SEGMENTS` in `hub/middleware.py` to prevent the middleware from misreading it as a business slug.

---

## Agent Migration — Completed

All 30 specialist AI agents have been migrated into this project (branch: `dev`, commit: `7c27051`).

### Source (read-only reference)
`d:\Bengal bound\Bengal Bound.worktrees\agents-constitutional-fox\api/agents/`

Each agent sub-app follows this pattern:
- `models.py` — domain models with FK to `'bredbound.BusinessInstance'`
- `views.py` — DRF ViewSets using `agent_chat()` from `agents.utils` (routes through LiteLLM)
- `serializers.py`, `urls.py`, `apps.py`, `migrations/`

### The 30 agents

| Agent | Role | Category |
|-------|------|----------|
| Aria | Customer Support Specialist | Support |
| Atlas | Executive Assistant | Operations |
| Babel | Translation & Localisation | Communication |
| Cash | Payroll Processing | Finance |
| Clarity | Customer Feedback Analysis | Analytics |
| Concierge | Front-door Receptionist | Operations |
| Content Architect | Editorial Planning | Marketing |
| Crux | CRM Manager | Sales |
| Dox | Technical Writer | Documents |
| Flux | Supply Chain Manager | Operations |
| Hera | HR Agent | HR |
| Kai | DevOps Assistant | Technology |
| Lead Hunter | B2B Prospector | Sales |
| Luma | Brand & PR | Marketing |
| MediBook | Medical Scheduler | Healthcare |
| Merch | eCommerce Manager | Commerce |
| Mira | Customer Success | Support |
| Nexus | Learning & Development | HR |
| Nova | Data Analyst | Analytics |
| Oracle | SEO Strategist | Marketing |
| Payload | Procurement Manager | Operations |
| Pulse | Market Research | Analytics |
| Realt | Real Estate Assistant | Real Estate |
| Reporting Bot | Automated Reporting | Analytics |
| Sage | Legal Reviewer | Legal |
| Scout | Competitor Intelligence | Analytics |
| Serea (Content) | Content Strategist | Marketing |
| Shield | IT Helpdesk | Technology |
| Tempo | Events Manager | Operations |
| Voice Receptionist | Phone AI Receptionist | Communication |

### Sprint summary

**Sprint A — Foundation** ✅
- [x] Create `agents/` Django app with `AgentCatalog` model
- [x] `seed_agents` management command (seeds all 30 into `AgentCatalog`)
- [x] Extend `HiredAIEmployee` with `agent_catalog` FK
- [x] Gemini added to `SEREA_TASK_MODELS`; `GEMINI_API_KEY` in `.env.example`

**Sprint B — Domain models** ✅
- [x] All 30 agents ported to `agents/<name>/models.py` with FK to `'bredbound.BusinessInstance'`
- [x] Initial migrations created and applied for all 30 agents

**Sprint C — AI call layer** ✅
- [x] `agents/utils.py` — `agent_chat()` wrapper calling LiteLLM proxy
- [x] All agent views use `agent_chat()` (no direct model provider calls)

**Sprint D — DRF API layer** ✅
- [x] All 30 agents: `serializers.py`, `views.py` (DRF ViewSets), `urls.py`
- [x] Mounted under `hub/<slug>/agents/<name>/` in root urlconf
- [x] `voice_receptionist` auth fixed — replaced Firebase dependency with DRF `SessionAuthentication`
- [x] `content_strategist` agent created (was missing from source; built from scratch)

**Sprint E — Console UI** (next)
- [ ] Agent marketplace browse page in `console_admin/`
- [ ] Per-agent dashboard views in hub templates
- [ ] Hire flow (`HiredAIEmployee` create view)
- [ ] Per-agent chat interface using `ConversationMessage`

**Sprint F — Inspector middleware**
- [ ] Port `api/inspector/` from worktree as new `inspector/` app
- [ ] Add to `MIDDLEWARE` in `base.py`
- [ ] `ComplianceRule` model + `seed_compliance_rules` command

**Sprint G — Stripe billing**
- [ ] Port `api/billing/` from worktree
- [ ] Add `stripe` to requirements
- [ ] Plan model tied to `BusinessSubscription` tiers

**Sprint H — Auth bridge**
- [ ] Add `firebase_uid` field to `accounts/models.py`
- [ ] Auth view accepting Firebase ID token → allauth user sync

**Recent Updates (Maintenance)**
- [x] Fixed `NoReverseMatch` 500 errors in `workspace_admin/views.py` missing namespace prefixes.
- [x] Ran `update_docs.py` replacing old hosting provider references with Cloud Run.
- [x] Pushed all changes to `origin`, `newhub`, and `showcase`.

---

*Walkthrough reflects the `dev` branch as of 2026-05-26. For line-accurate behavior, follow the linked source files.*
