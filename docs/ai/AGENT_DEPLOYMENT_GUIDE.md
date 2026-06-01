# Agent Deployment & Configuration Guide
# BengalBound HUB — BengalBound Ltd
**Version:** 1.0 | **Date:** June 2026 | **Audience:** Developers + CTO

---

## Overview

This guide covers how to configure, test, and deploy the 33 AI agents in BengalBound HUB. All agents share the same deployment pattern — they differ only in their system prompts and task types.

---

## Agent Architecture Pattern

Every agent lives at `agents/<name>/` and follows this structure:

```
agents/
  <name>/
    __init__.py
    apps.py           ← AppConfig name = 'agents.<name>'
    engine.py         ← Core agent logic, uses agent_chat()
    tasks.py          ← Celery task definitions
    models.py         ← Domain models (FK → 'bredbound.BusinessInstance')
    views.py          ← DRF ViewSets
    serializers.py
    urls.py           ← app_name = '<name>'
    migrations/
```

---

## The Only Correct Way to Call AI — LangChain (P2+)

All AI calls go through `agents/utils.py` using **LangChain 1.x** (LangGraph under the hood).

```python
from agents.utils import agent_chat

# Basic call (universal tools: web search, scrape, API)
result = agent_chat(
    messages=[
        {"role": "system", "content": "You are Crux, a world-class CRM manager..."},
        {"role": "user",   "content": "Audit this pipeline and flag stale deals."},
    ],
)

# With hub data access (agents that need live business data)
result = agent_chat(
    messages=[...],
    business=business_instance,   # scopes all ORM queries to this tenant
    agent_slug="crux",            # selects the correct hub tools (CRM, HR, Invoice, etc.)
)
```

### LLM routing

| Environment | LLM used |
|---|---|
| Dev / Render | `ChatGroq` → `meta-llama/llama-4-scout-17b-16e-instruct` (30k TPM free) |
| VPS (prod) | `ChatOpenAI` → LiteLLM proxy at `LITELLM_BASE_URL` |

`get_llm()` in `agents/utils.py` handles the routing automatically based on whether `LITELLM_BASE_URL` is set to a non-localhost URL.

**Never call Groq, OpenAI, or Gemini directly.** Always use `agent_chat()`.

---

## Adding a New Agent

### Step 1: Create the app structure

```bash
mkdir -p agents/myagent
touch agents/myagent/__init__.py
```

### Step 2: Write `apps.py`

```python
from django.apps import AppConfig

class MyAgentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agents.myagent'
    label = 'myagent'
    verbose_name = 'My Agent'
```

### Step 3: Add to `INSTALLED_APPS` in `base.py`

```python
INSTALLED_APPS = [
    ...
    'agents.myagent',
]
```

### Step 4: Add to `AgentCatalog` seed

Edit `agents/management/commands/seed_agents.py` and add your agent's entry to the `AGENTS` list:

```python
{
    'name': 'My Agent',
    'slug': 'myagent',
    'role': 'Description of what this agent does',
    'description': 'Longer description for the marketplace',
    'system_prompt': 'You are My Agent, an expert in...',
    'category': 'Operations',
    'tier_required': 'entry',
    'icon': 'bi-robot',
    'is_active': True,
},
```

### Step 5: Run migrations and seed

```bash
python manage.py makemigrations myagent
python manage.py migrate
python manage.py seed_agents
```

---

## Testing an Agent Locally

```python
# In Django shell: python manage.py shell
from agents.utils import agent_chat

# Quick smoke test
result = agent_chat([
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user",   "content": "Say hello and confirm you are working."},
])
print(result)
```

Expected output: A friendly response confirming the agent is working. If you get a `401` or `503`, check your `GROQ_API_KEY` in `.env`.

---

## Agent Configuration Per Tenant

Each tenant configures their hired agents via `HiredAIEmployee`:

```python
# Key model fields
class HiredAIEmployee(models.Model):
    employer       = models.ForeignKey('bredbound.BusinessInstance', ...)
    agent_catalog  = models.ForeignKey('agents.AgentCatalog', ...)
    custom_prompt  = models.TextField(blank=True)   # tenant override
    schedule       = models.CharField(...)           # cron expression
    tokens_used    = models.IntegerField(default=0)
    is_active      = models.BooleanField(default=True)
```

When `custom_prompt` is set, it appends to the base `system_prompt` from `AgentCatalog`. This lets tenants customize agent behavior without changing shared code.

---

## Celery Beat Scheduling

Agents run on a schedule via Celery Beat. Each agent's `tasks.py` defines its periodic task:

```python
# agents/crux/tasks.py
from celery import shared_task
from agents.utils import agent_chat

@shared_task
def run_crux_pipeline_audit(business_id: int):
    # 1. Fetch stale deals for this business
    # 2. Call agent_chat() with context
    # 3. Save results, notify console
    ...
```

Celery Beat config in `base.py`:
```python
CELERY_BEAT_SCHEDULE = {
    'crux-daily-audit': {
        'task': 'agents.crux.tasks.run_crux_pipeline_audit',
        'schedule': crontab(hour=8, minute=0),
    },
    ...
}
```

**Note:** On Render free tier, Celery runs eagerly (synchronous). On VPS production, a real Redis + Celery worker is required.

---

## Inspector Gate — Every Agent Must Pass

All mutating agent actions (writes, sends, updates) must pass through the Inspector:

```
Agent Action
    │
    ▼
InspectorMiddleware (inspector/middleware.py)
    │
    ├── 5 checks: Legal · Ethics · Cybersecurity · Data Privacy · Harm Prevention
    │
    ├── PASS → agent_chat() executes
    └── BLOCK → 403, audit log written, console notification sent
```

Inspector uses `phi4-mini` key → `llama-4-scout-17b` for fast classification. Every decision is SHA-256 chained in `inspector_compliancecheck` — immutable, never deletable.

---

## Hub Data Tools — P2 Agent→Module Connectors

`agents/hub_tools.py` provides LangChain `StructuredTool` instances scoped to a specific business. Each tool hits real Django ORM — no mocked data.

| Agent Slug | Hub Tools Available |
|---|---|
| `crux`, `lead-hunter` | `crm_get_contacts`, `crm_get_deals`, `crm_pipeline_summary`, `crm_create_contact`, `crm_log_activity` |
| `hera`, `nexus` | `hr_get_employees`, `hr_pending_leaves`, `hr_headcount`, `hr_performance_reviews` |
| `cash` | `invoice_list`, `invoice_revenue_summary`, `invoice_client_balance` |
| `reporting-bot`, `nova`, `clarity` | All CRM + HR + Invoice tools |
| All others | Universal tools only (web search, scrape, API call) |

Tools are added automatically by `agent_chat(business=..., agent_slug=...)` — no changes needed in engine.py files.

---

## Environment Variables for Agents

| Variable | Purpose | Required |
|---|---|---|
| `GROQ_API_KEY` | Direct Groq inference (dev/Render) | Yes |
| `LITELLM_BASE_URL` | HTTP proxy URL (VPS prod only) | Optional |
| `LITELLM_MASTER_KEY` | Proxy auth key | If proxy set |
| `SEREA_MODEL_CHAT` | Override default model key | No |

---

## 33 Deployed Agents — Status (June 2026)

All 33 agents are implemented, seeded, and verified working as of 2026-05-29.

| Category | Agents |
|---|---|
| Support | aria, mira, concierge |
| Sales | crux, lead-hunter |
| HR | hera, nexus, cash |
| Marketing | luma, serea-content, content-architect, oracle |
| Analytics | clarity, nova, pulse, scout, reporting-bot |
| Operations | atlas, flux, payload, tempo |
| Finance | (via cash + reporting-bot) |
| Technology | kai, shield |
| Documents | dox |
| Legal | sage |
| Specialist | medibook, merch, realt, babel |
| Communication | voice-receptionist |

---

*BengalBound HUB — Agent Deployment Guide v1.0 — June 2026*
