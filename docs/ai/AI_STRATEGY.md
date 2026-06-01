# AI & Agent Framework Strategy
# BengalBound HUB — BengalBound Ltd
**Updated:** June 2026

---

## 1. Overview

BengalBound HUB uses a **dual-mode AI architecture**: in development and on free-tier hosting, AI calls go directly through the `litellm` Python library to Groq (using `GROQ_API_KEY`). In production with a proxy server, calls route through an HTTP LiteLLM proxy at `LITELLM_BASE_URL`. The same `agent_chat()` function handles both modes transparently.

**Dev / Render (no proxy server):** `GROQ_API_KEY` → `litellm` library → Groq `meta-llama/llama-4-scout-17b-16e-instruct` (30k TPM free)
**Production (with proxy):** `LITELLM_BASE_URL` (remote) → HTTP proxy → Groq / OpenRouter / Gemini

This gives us:

- **Provider agnosticism** — swap models without touching agent code
- **Zero-cost dev** — Groq free tier handles all 33 agents in development
- **Cost control** — route cheap tasks to faster/cheaper models, premium tasks to better ones
- **Offline-capable** — add Ollama as a LiteLLM backend for zero-cost local inference

### Financial Model

| Approach | Variable cost per 1M tokens | Gross margin at 100 clients |
|---|---|---|
| Direct Gemini API only | ~$0.075–$0.15 | 70–80% |
| Ollama via LiteLLM (self-hosted) | $0 (fixed server cost) | 98%+ |
| **LiteLLM hybrid (our approach)** | ~$0.001 blended | **98%+** |

> At 100 clients, infrastructure + AI cost is ~$219/month total. Revenue ~$12,600/month. **98% gross margin**.

---

## 2. AI Engine Architecture

All AI calls in BengalBound HUB go through a single utility function:

```python
# agents/utils.py — THE ONLY correct way to call any AI
from agents.utils import agent_chat

result = agent_chat(
    messages=[
        {"role": "system", "content": "You are Serea, a world-class content strategist..."},
        {"role": "user", "content": "Write a LinkedIn post about AI"},
    ],
    model=None  # None = use default from SEREA_TASK_MODELS
)
```

**Never call Gemini, Groq, or OpenAI directly. Always use `agent_chat()`.**

### Model Routing (via `SEREA_TASK_MODELS` in `base.py`)

```python
SEREA_TASK_MODELS = {
    'chat':       env('SEREA_MODEL_CHAT',       default='neural-chat'),
    'moderation': env('SEREA_MODEL_MODERATION', default='dolphin-mistral'),
    'content':    env('SEREA_MODEL_CONTENT',    default='glm4'),
    'analysis':   env('SEREA_MODEL_ANALYSIS',   default='qwen2.5-coder'),
    'quick':      env('SEREA_MODEL_QUICK',      default='phi4-mini'),
    'gemini':     env('GEMINI_MODEL',           default='gemini/gemini-1.5-flash'),
}
```

All of these nickname keys map to `groq/meta-llama/llama-4-scout-17b-16e-instruct` when running via the direct litellm library path (dev / Render). In production with a proxy, each key can be routed to a different model.

| Task type | Nickname key | Dev model (Groq direct) | Prod model (proxy, configurable) |
|---|---|---|---|
| `chat` | `neural-chat` | llama-4-scout-17b | Any proxied model |
| `moderation` | `dolphin-mistral` | llama-4-scout-17b | Lighter fast model |
| `content` | `glm4` | llama-4-scout-17b | Content-optimised model |
| `analysis` | `qwen2.5-coder` | llama-4-scout-17b | Code/analysis model |
| `quick` | `phi4-mini` | llama-4-scout-17b | Fast classification model |
| `gemini` | `gemini/gemini-1.5-flash` | llama-4-scout-17b | Gemini for vision/reasoning |

---

## 3. AI Provider Strategy

### Dev / Render Free Tier (Current — No Proxy Required)

`GROQ_API_KEY` is the only required key. The `litellm` Python library calls Groq directly:

| Provider | Model | Free Tier |
|---|---|---|
| Groq | `meta-llama/llama-4-scout-17b-16e-instruct` | 30,000 TPM free |

### Production with LiteLLM Proxy (Optional)

When `LITELLM_BASE_URL` points to a remote proxy, all calls go through it:

| Provider | Models | Use Case |
|---|---|---|
| Groq | `neural-chat`, `llama-4-scout` | Fast inference |
| OpenRouter | `glm4`, `qwen2.5-coder`, `phi4-mini` | Cheap bulk tasks |
| Gemini | `gemini/gemini-1.5-flash` | Premium, vision, overflow |

### Growth (Add to LiteLLM config)
| Provider | Models | Use Case |
|---|---|---|
| Ollama (self-hosted VPS) | `mistral:7b`, `llama3:8b` | Zero variable cost, private |
| OpenAI | `gpt-4o-mini` | Fallback for highest-quality tasks |

### Adding Ollama to LiteLLM
```yaml
# litellm_config.yaml on the LiteLLM proxy server
model_list:
  - model_name: neural-chat
    litellm_params:
      model: ollama/mistral:7b
      api_base: http://localhost:11434
  - model_name: gemini/gemini-1.5-flash
    litellm_params:
      model: gemini/gemini-1.5-flash
      api_key: os.environ/GEMINI_API_KEY
```

---

## 4. Agent Ecosystem

BengalBound HUB hosts 33 specialist AI employees, each for a specific business vertical. All 33 are implemented, seeded, and verified working (as of 2026-05-29).

### Core Principles
- **No Hallucination:** Agents use structured outputs and rely on factual context via the hub's module data
- **Fail-Closed:** If uncertain, escalate to human console — never guess or bypass Inspector
- **Inspector First:** Every mutating agent action passes through `inspector.middleware.InspectorMiddleware`
- **Provider-Agnostic:** All agents use `agent_chat()` — swap models without touching agent code
- **Tenant-scoped:** Every agent action scoped to `bredbound.BusinessInstance` — no cross-tenant data access

### Implementation Status — All 33 Agents Complete (June 2026)

All sprints are complete. All 33 agents are implemented, seeded, and verified working as of 2026-05-29.

| Batch | Agents | Status |
|---|---|---|
| Customer-facing | Aria, Crux, Mira, Lead Hunter | ✅ Done |
| Finance & HR | Cash, Payload, Hera, Nexus | ✅ Done |
| Content & Intelligence | Content Architect, Oracle, Nova, Scout, Clarity, Pulse, Luma | ✅ Done |
| Specialist | Sage, Dox, Babel, Realt, MediBook, Merch, Shield, Kai, Flux, Atlas, Tempo, Voice Receptionist, Reporting Bot | ✅ Done |

---

## 5. Inspector — AI Compliance Engine

Every non-GET request from an agent is intercepted by Inspector before execution.

- **Location:** `inspector/middleware.py` → `InspectorMiddleware`
- **Regulations:** 40+ laws — GDPR · HIPAA · EU AI Act · PDPA (SG) · LGPD (BR) · BD CPO + 35 more
- **AI model:** Runs on `phi4-mini` (fast classification) with Gemini fallback for complex cases via LiteLLM
- **Output:** ALLOW | BLOCK | FLAG (for human review)
- **Audit log:** Every decision is immutable, SHA-256 chained, never deletable

See [`docs/platform/inspector_compliance_monitor.md`](../platform/inspector_compliance_monitor.md) for full spec.

---

## 6. VPS Infrastructure & Scaling

### Startup Deployment (Hetzner CX42 — 16GB RAM)
```
Nginx → Gunicorn (Django 4.2) → LiteLLM proxy (Groq/OpenRouter)
                              → PostgreSQL (local)
                              → Celery + Redis (Beat tasks)
```

### Growth (Add Ollama on same or dedicated VPS)
```
Nginx → Gunicorn → LiteLLM proxy → Ollama (local, port 11434)
                                  → Groq/OpenRouter (overflow)
                                  → Gemini API (premium)
```

### VPS Scaling Path

| Stage | Server | Specs | Cost | Clients |
|---|---|---|---|---|
| Startup | Hetzner CX42 | 8 vCPU · 16GB RAM · 160GB SSD | $19/mo | 0–50 |
| Growth | Hetzner AX52 | 12 vCPU · 64GB RAM · 512GB NVMe | $56/mo | 50–300 |
| Scale | Hetzner AX102 ×2 | 24 vCPU · 128GB RAM · 1TB NVMe | $292/mo | 300–1,000 |
| Enterprise | Hetzner GPU (RTX 4000) | GPU · 64GB · 1TB | $380/mo | 1,000+ |

---

## 7. NGO / Social Enterprise AI Commitment

BengalBound offers a free AI tier for registered Bangladeshi NGOs:

- **Social mission:** 500,000+ NGOs in Bangladesh cannot afford human staff
- **Business strategy:** Each NGO = case study = press coverage = grant eligibility
- **Grant pathway:** Free NGO tier enables eligibility for USAID, Gates Foundation, Google.org grants

AI models used for NGO tier: `phi4-mini` key → `llama-4-scout-17b` via Groq (free 30k TPM — zero variable cost at this scale).

---

*BengalBound HUB — AI Strategy v1.3 — Updated June 2026*
