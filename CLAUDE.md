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

## Agent Migration (Active Sprint)

We are migrating 30 AI agents from a separate codebase into this project.
**Source** (read-only — never edit): `d:\Bengal bound\Bengal Bound.worktrees\agents-constitutional-fox\api/agents/`

### New app: `agents/`
All 30 agents live under `agents/<name>/` in this repo.

### Pattern for every agent app

```
agents/
  <name>/
    __init__.py
    apps.py           ← AppConfig name = 'agents.<name>'
    models.py         ← Domain models, FK to 'bredbound.BusinessInstance'
    views.py          ← DRF ViewSets, uses agent_chat() from agents.utils
    serializers.py
    urls.py           ← app_name = '<name>'
    migrations/
```

### AgentCatalog model (Sprint A — DO FIRST)
```python
class AgentCatalog(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    role = models.CharField(max_length=200)
    description = models.TextField()
    system_prompt = models.TextField()
    category = models.CharField(max_length=100)
    tier_required = models.CharField(max_length=20, default='entry')
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=50, blank=True)
```

### The 30 agents (Sprint A seeds all of these)

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

# Seed AI agent catalog (30 agents) — Sprint A
python manage.py seed_agents

# Standard
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic    # Production only
```

---

## Key File Locations

| Purpose | File |
|---------|------|
| Installed apps + middleware | `bengalbound_core/settings/base.py` |
| Root URL table | `bengalbound_core/urls.py` |
| Business middleware | `hub/middleware.py` |
| Module sidebar routing | `hub/context_processors.py` |
| Module seeder | `hub/management/commands/seed_modules.py` |
| Agent seeder | `agents/management/commands/seed_agents.py` (Sprint A) |
| AI utility | `agents/utils.py` (Sprint C) |
| LiteLLM AI models | `SEREA_TASK_MODELS` in `bengalbound_core/settings/base.py` |
| Env template | `.env.example` |

---

## DO NOT
- Call AI models directly (use LiteLLM proxy only)
- Use `'hub.BusinessInstance'` as FK target (use `'bredbound.BusinessInstance'`)
- Edit files in `d:\Bengal bound\Bengal Bound.worktrees\agents-constitutional-fox\` (read-only source)
- Push to GitHub without explicit user approval
- Run on any port other than 1234 in dev
