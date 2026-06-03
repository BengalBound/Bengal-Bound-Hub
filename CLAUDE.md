# Claude Code — BengalBound HUB

This file configures Claude Code (and any AI assistant) working on the BengalBound HUB project.

---

## Project Identity

**BengalBound HUB** is a Django 4.2 LTS multi-tenant SaaS business operating system. It serves multiple surfaces via subdomain routing, provides 60+ pluggable business modules, and will host a 30-agent AI Employee Marketplace built on Serea + LiteLLM.

**This is the primary working repository.** All new development — including the 30 AI agents — goes here.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django **4.2 LTS** |
| Auth | django-allauth (email + Google / Facebook / GitHub OAuth) |
| AI | Serea + **LiteLLM proxy** at `LITELLM_BASE_URL` |
| Task Queue | Celery + Redis |
| Database | SQLite (dev) / PostgreSQL (production via `DATABASE_URL`) |
| Templates | Django templates (DRF API layer in progress) |
| Security | django-axes, django-otp, django-simple-history, django-encrypted-model-fields |

---

## Critical Rules for All Edits

### 1. App label — never change
The `hub/` folder has Django app label `bredbound` (set in `hub/apps.py`).
All module ForeignKeys use `'bredbound.BusinessInstance'` — **not** `'hub.BusinessInstance'`.
Never rename the folder or the label.

### 2. AI calls — always through LiteLLM
**Never** call Groq, OpenAI, Gemini, or any model provider directly.
All AI calls go through the LiteLLM proxy:

```python
# agents/utils.py — the ONLY way to call AI
import requests
from django.conf import settings

def agent_chat(messages: list, model: str = None) -> str:
    model = model or settings.SEREA_TASK_MODELS.get('chat', 'neural-chat')
    resp = requests.post(
        f"{settings.LITELLM_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"},
        json={"model": model, "messages": messages},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
```

### 3. Suite-first URL middleware
If you add a new module as a suite-first URL (`hub/<prefix>/<slug>/`), add `<prefix>` to `_SKIP_SEGMENTS` in `hub/middleware.py` — otherwise `BusinessAccessMiddleware` will misread it as a business slug.

### 4. Module views pattern
Every view in every module must accept `(request, slug)` and verify business access:
```python
def index(request, slug):
    business = get_object_or_404(BusinessInstance, slug=slug)
    employee = get_object_or_404(BusinessEmployee, business=business, user=request.user)
    ...
```

### 5. Settings are split
- `bengalbound_core/settings/base.py` — shared config, edit here for new settings
- `bengalbound_core/settings/development.py` — dev overrides only
- `bengalbound_core/settings/production.py` — production hardening only
- Never add secrets to `base.py`

### 6. Dev server port
Run on **port 1234**: `python manage.py runserver 0.0.0.0:1234`
`CSRF_TRUSTED_ORIGINS` is configured for port 1234.

---

## Sprint Status (as of 2026-06-03)

**ALL Sprints A–H are COMPLETE.** The agent migration is done.

| Sprint | What | Status |
|--------|------|--------|
| A | AgentCatalog model + 30 agents seeded | ✅ Done |
| B | Agent sub-apps created (engine.py + tasks.py per agent) | ✅ Done |
| C | agents/utils.py + CELERY_BEAT_SCHEDULE for all agents | ✅ Done |
| D | DRF ViewSets, serializers, urls per agent | ✅ Done |
| E | Agent sprint E tests + coverage | ✅ Done |
| F | WebSocket real-time permission resolution | ✅ Done |
| G | Stripe billing integration (checkout, webhooks, success/cancel pages) | ✅ Done |
| H | Firebase auth bridge (firebase_token_sync, firebase_uid on User model) | ✅ Done |
| **I** | **Veritas KYB module — NEXT SPRINT** | 🔲 Not started |

---

## Next Sprint: Veritas KYB (Sprint I)

Veritas is the **critical gate** — no AI agent can activate until a client has Green KYB clearance.
Spec: `docs/platform/veritas_client_kyb_onboarding.md`

### New app: `veritas/`

```
veritas/
  __init__.py
  apps.py           ← app_name = 'veritas'
  models.py         ← ClientApplication, KYBDocument, SanctionsCheck, ClientAgreement
  views.py          ← Application submit, document upload, status check, sign agreements
  serializers.py
  urls.py           ← app_name = 'veritas'
  tasks.py          ← async Celery tasks: registry_check, sanctions_scan, risk_score
  engine.py         ← AI-powered document OCR + risk analysis via agent_chat()
  migrations/
```

### Core models (from SRS)
- `ClientApplication` — status choices: submitted → under_review → approved/rejected/amber
- `KYBDocument` — uploaded docs (trade license, passport, etc.) with AI verification
- `SanctionsCheck` — OFAC/UN/EU/FATF screening results
- `ClientAgreement` — digital signatures on TOS, DPA, AUP, AI Ethics docs

### Inspector gate in veritas
Before any AI agent endpoint: check `ClientApplication.status == 'approved'` — if not, return `HTTP 403 KYB Required`.

### After Veritas: Sprint J — bKash Payment
The primary payment method for the Bangladesh market. Stripe handles global; bKash handles BD.
Spec: `docs/architecture/FULL_AUTOMATION.md` (billing section).

---

## Completed Agent Apps

All 30 agents are in `agents/<name>/` with full engine.py + tasks.py pattern:

| Slug | Name | Category |
|------|------|----------|
| `aria` | Customer Support | Support |
| `atlas` | Executive Assistant | Operations |
| `babel` | Translation Specialist | Communication |
| `cash` | Payroll Processor | Finance |
| `clarity` | Feedback Analyst | Analytics |
| `concierge` | Client Concierge | Operations |
| `content-architect` | Content Strategist | Marketing |
| `crux` | CRM Manager | Sales |
| `dox` | Technical Writer | Documents |
| `flux` | Supply Chain Manager | Operations |
| `hera` | HR Agent | HR |
| `kai` | DevOps Engineer | Technology |
| `lead-hunter` | B2B Prospector | Sales |
| `luma` | Brand & PR | Marketing |
| `medibook` | Medical Scheduler | Healthcare |
| `merch` | eCommerce Manager | Commerce |
| `mira` | Customer Success | Support |
| `nexus` | L&D Coordinator | HR |
| `nova` | Data Scientist | Analytics |
| `oracle` | SEO Specialist | Marketing |
| `payload` | Procurement Manager | Operations |
| `pulse` | Market Research | Analytics |
| `realt` | Real Estate Assistant | Real Estate |
| `reporting-bot` | Automated Reporting | Analytics |
| `sage` | Legal Reviewer | Legal |
| `scout` | Competitor Intel | Analytics |
| `serea-content` | Content Strategist | Marketing |
| `shield` | IT Helpdesk | Technology |
| `tempo` | Events Manager | Operations |
| `voice-receptionist` | Phone Receptionist | Communication |

---

## Management Commands

```bash
# Seed business modules (60+)
python manage.py seed_modules

# Seed AI agent catalog (30 agents)
python manage.py seed_agents

# Seed Inspector compliance rules (40+ global laws)
python manage.py seed_compliance_rules

# Standard
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic    # Production only

# Run tests (use development settings — testing.py also works)
python manage.py test --settings=bengalbound_core.settings.development
```

---

## Key File Locations

| Purpose | File |
|---------|------|
| Installed apps + middleware | `bengalbound_core/settings/base.py` |
| Root URL table | `bengalbound_core/urls.py` |
| Workspace URL table | `bengalbound_core/workspace_urls.py` |
| Business middleware | `hub/middleware.py` |
| Inspector middleware | `inspector/middleware.py` |
| Module sidebar routing | `hub/context_processors.py` |
| Module seeder | `hub/management/commands/seed_modules.py` |
| Agent seeder | `agents/management/commands/seed_agents.py` |
| Compliance rules seeder | `inspector/management/commands/seed_compliance_rules.py` |
| AI utility | `agents/utils.py` |
| Inspector compliance gate | `inspector/views.py` → `run_compliance_evaluation()` |
| Stripe billing | `billing/views.py`, `billing/services.py` |
| Firebase auth bridge | `accounts/views.py` → `firebase_token_sync()` |
| Hub DRF API | `hub/api_views.py`, `hub/api_urls.py` (namespace: `api:hub_api`) |
| Agent catalog API | `agents/global_api_urls.py` (namespace: `api:agents_global_api`) |
| LiteLLM AI models | `SEREA_TASK_MODELS` in `bengalbound_core/settings/base.py` |
| Env template | `.env.example` |

---

## DO NOT
- Call AI models directly (use LiteLLM proxy only)
- Use `'hub.BusinessInstance'` as FK target (use `'bredbound.BusinessInstance'`)
- Edit files in `d:\Bengal bound\Bengal Bound.worktrees\agents-constitutional-fox\` (read-only source)
- Push to GitHub without explicit user approval
- Run on any port other than 1234 in dev
