# BengalBound HUB — CTO Technical Briefing
# BengalBound Ltd | "Light. Easy. Powerful."

> **Document Class:** System Architecture & Infrastructure Spec  
> **Prepared for:** Chief Technology Officer (CTO) & Lead Architects  
> **Prepared by:** Principal AI Infrastructure Architect  
> **Date:** May 2026 | **Version:** 1.0  

---

## 🏗️ 1. Global System Topology

BengalBound HUB runs a decoupled, subdomain-routed Django architecture serving multiple surfaces:

```
                  [ PUBLIC REQUEST ]
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
      [ MAIN DOMAIN ]           [ SUBDOMAINS ROUTER ]
  public_site (Marketing)        SubdomainRoutingMiddleware
             │                           │
             ▼                           ├── workspace.* ➔ workspace_urls
   [ /hub/<slug>/ paths ]                ├── console.*   ➔ console_urls
  BusinessAccessMiddleware               └── community.* ➔ community_urls
             │
             ├── Validates allowed_ips for IP-locked instances
             └── Resolves request.current_business (bredbound.BusinessInstance)
```

---

## 🔒 2. Data Security & Multi-Tenancy Controls

### Multi-Tenancy Architecture
*   **Database Isolation:** All dynamic modules (CRM, ERP, Attendance, etc.) map directly to `'bredbound.BusinessInstance'` via a Foreign Key relation. Cross-tenant database access is prevented via custom Django Managers that filter querysets implicitly by the resolved tenant instance.
*   **Audit Trails:** Built-in `django-simple-history` tracks all mutations on core models (`BusinessInstance`, `BusinessEmployee`), storing immutable revision tables for operational compliance auditing.
*   **Encrypted Credentials:** Client external credentials (API keys, passwords) are encrypted at rest using Fernet encryption (`django-encrypted-model-fields`) linked to the secure project environmental key.

---

## 🤖 3. LiteLLM & AI Scaling Strategy

### Blended Model Routing Schema
We operate a centralized AI routing layer inside `agents.utils.agent_chat()`. This decouples the agent logic from underlying API models.

**Dev / Render (no proxy):** `GROQ_API_KEY` → litellm library → Groq `meta-llama/llama-4-scout-17b-16e-instruct` (30k TPM free)
**Production (proxy set):** `LITELLM_BASE_URL` → HTTP proxy → routed model per task key

```python
# settings/base.py
SEREA_TASK_MODELS = {
    'chat':       env('SEREA_MODEL_CHAT',       default='neural-chat'),
    'moderation': env('SEREA_MODEL_MODERATION', default='dolphin-mistral'),
    'content':    env('SEREA_MODEL_CONTENT',    default='glm4'),
    'analysis':   env('SEREA_MODEL_ANALYSIS',   default='qwen2.5-coder'),
    'quick':      env('SEREA_MODEL_QUICK',      default='phi4-mini'),
    'gemini':     env('GEMINI_MODEL',           default='gemini/gemini-1.5-flash'),
}
```

In dev, all nickname keys resolve to `groq/meta-llama/llama-4-scout-17b-16e-instruct` via the `_GROQ_MODEL_MAP` in `agents/utils.py`.

### Infrastructure Scaling Benchmark Targets

| Milestone | VPS Specs | Stack Configurations | Peak Parallel Requests | Blended Monthly Cost |
|---|---|---|---|---|
| **Beta (1–50 clients)** | Hetzner CX42 (8 vCPUs, 16GB RAM) | SQLite (Dev) + Gunicorn + Celery + Redis + LiteLLM (Cloud) | 50 req/sec | $19 USD |
| **Scale (50–300 clients)** | Hetzner AX52 (12 vCPUs, 64GB RAM) | PostgreSQL + Celery (Redis Broker) + local Ollama backend | 250 req/sec | $56 USD |
| **Enterprise (300+ clients)** | Dedicated AX102 Cluster | Postgres Cluster + HA Redis + Dedicated Ollama (RTX 4000 GPU) | 1,000+ req/sec | $292 USD |

---

## ⚡ 4. Inspector — The AI Compliance Watchdog

All mutating actions (non-GET request endpoints) triggered by AI employees undergo interceptor audits inside `inspector/middleware.py`:

```
 [ Agent Trigger Action ] ➔ [ Inspector Interception ]
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
         [ Risk Classification ]            [ Compliance Assessment ]
         - Redacts PII                     - Checks 40+ Laws (GDPR, HIPAA)
         - Flags high-risk mutations       - Uses phi4-mini / Gemini
                    │
           ┌────────┴────────┐
           ▼                 ▼
      [ ALLOW ]         [ BLOCK / FLAG ]
    Direct execution    Human-in-the-loop approval required
```

Every Inspector decision is immunely logged as a SHA-256 chained transaction within the local database to serve as an immutable compliance record.
