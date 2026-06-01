# System Architecture & Diagrams
# BengalBound HUB — BengalBound Ltd
**Version:** 2.1 | Updated: June 2026 | ISO/IEC 25010 Aligned

---

## 1. Platform Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BENGALBOUND HUB PLATFORM                             │
│                         Powered by BengalBound Ltd                          │
└─────────────────────────────────────────────────────────────────────────────┘

  CLIENT TOUCHPOINTS                  PLATFORM CORE                  EXTERNAL
  ─────────────────                   ─────────────              ──────────────
  domain.com           ──────────►  [Marketing Site / Hub]
  (Django templates)                   │
                                        │ Login (allauth)
  workspace.domain     ──────────►  [Workspace Admin]   ◄──  Internal ops only
  (Django templates)                   │
                                        │
  console.domain       ──────────►  [Customer Console]
  (Django templates)                   │
                                        │ Hub modules
  /hub/<slug>/...      ──────────►  [BusinessInstance]   ◄──  60+ modules/
                                        │
                                   ┌───▼───────────────┐
                                   │    INSPECTOR       │ ◄── LiteLLM proxy
                                   │  (Always-On Gate)  │     (compliance check)
                                   └───┬───────────────┘
                                       │ If PASS
                                   ┌───▼───────────────┐
                                   │  AI CALL LAYER     │
                                   │  agents/utils.py   │ ◄── LiteLLM proxy
                                   │  agent_chat()      │     LITELLM_BASE_URL
                                   └───┬───────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                           ▼
     [Aria Agent]              [Crux Agent]               [Serea Engine]  ...30
     Support tickets           CRM management             Social content
            │                          │                           │
            └──────────────────────────┴──────────────────────────┘
                                       │
                               ┌───────▼───────┐
                               │  PostgreSQL    │
                               │  (production)  │
                               │  SQLite (dev)  │
                               └───────────────┘
```

---

## 2. Subdomain Routing Architecture

```
Browser Request
    │
    ▼
SubdomainRoutingMiddleware (bengalbound_core/middleware.py)
    │
    ├── workspace.domain ──► workspace_urls.py
    │                           └── /workspace/... (internal ops)
    │                           └── Django admin
    │
    ├── console.domain   ──► console_urls.py
    │                           └── /console/... (customer dashboard)
    │                           └── /serea/... (AI chat)
    │
    ├── community.domain ──► community_urls.py
    │                           └── /community/... (forum)
    │
    └── (default host)   ──► urls.py (ROOT_URLCONF)
                                └── / (public site)
                                └── /hub/<slug>/... ──► BusinessAccessMiddleware
                                                           └── Views + Templates
```

**Deployment:**
- Backend: Render free tier (`render.yaml`, `bengalbound_core/settings/render.py`, Supabase PostgreSQL)
- Public site: Netlify (`netlify.toml`, export via `python manage.py export_static --settings=netlify_settings`)
- AI: Groq `meta-llama/llama-4-scout-17b-16e-instruct` (30k TPM free) via litellm library; LiteLLM proxy optional for VPS prod

**Dev setup** — add to `C:\Windows\System32\drivers\etc\hosts`:
```
127.0.0.1  workspace.localhost
127.0.0.1  console.localhost
127.0.0.1  community.localhost
```
Run on **port 1234**: `python manage.py runserver 0.0.0.0:1234`

---

## 3. Request Flow: Every AI Agent Action

```
Client Console (console.domain)
    │
    │ POST /hub/<slug>/api/agents/<name>/tasks/<id>/process/
    ▼
 ┌─────────────┐
 │ Django API   │
 │ Auth Check   │ ──── FAIL ──► 401 Unauthorized
 └──────┬──────┘  (allauth session / DRF token)
        │ PASS
        ▼
 ┌─────────────┐
 │ Business    │
 │ Access      │ ──── FAIL ──► 403 Forbidden
 │ Check       │  (BusinessEmployee verification)
 └──────┬──────┘
        │ PASS
        ▼
 ┌─────────────┐        ┌────────────────────────┐
 │  INSPECTOR  │──────► │ 5-Check Pipeline:       │
 │    GATE     │        │ 1. Legal compliance     │
 └──────┬──────┘        │ 2. Ethics check         │
        │               │ 3. Cybersecurity risk   │
        │               │ 4. Data privacy         │
        │               │ 5. Harm prevention      │
        │               └────────────┬───────────┘
        │          ┌─────────────────┴──────────────┐
        │          │                                  │
        │        PASS                               BLOCK
        │          │                                  │
        │          │                    ┌─────────────▼──────────┐
        │          │                    │ Log to audit trail      │
        │          │                    │ Notify workspace admin  │
        │          │                    │ Return 403 to agent     │
        │          │                    │ Notify client console   │
        │          │                    └─────────────────────────┘
        ▼          ▼
 ┌─────────────────────┐
 │  agent_chat()        │
 │  agents/utils.py     │ ──► LiteLLM proxy at LITELLM_BASE_URL
 └──────────┬──────────┘        └── Routes to Groq/OpenRouter/Gemini
            │
            ▼
 ┌─────────────────────┐
 │  Agent Executes      │
 │  Action              │
 └──────────┬──────────┘
            │
            ▼
 ┌─────────────────────┐
 │  Save to DB          │
 │  ComplianceCheck log │
 │  Return to Console   │
 └─────────────────────┘
```

---

## 4. Client Onboarding Flow

```
         domain.com
            │
            ▼
    ┌───────────────┐
    │   Sign Up     │ ─── Email+Password OR Google/Facebook/GitHub OAuth
    └───────┬───────┘      (django-allauth)
            │
            ▼
    ┌───────────────┐
    │Email Verified?│ ── NO ──► Send verification email → Wait
    └───────┬───────┘
            │ YES
            ▼
    ┌───────────────────────────┐
    │   VERITAS KYB GATE        │
    │ Company name + country    │
    │ Registration number       │
    │ Director NID/Passport     │
    │ Document upload           │
    └───────────┬───────────────┘
                │
      ┌─────────┼──────────┐
      ▼         ▼          ▼
   🟢 AUTO   🟡 MANUAL   🔴 REJECT
   APPROVE    REVIEW
      │         │
      │      Workspace admin reviews
      │         │
      └────┬────┘
           ▼
    ┌──────────────┐
    │ Create       │
    │ BusinessInstance│
    │ (slug, tier) │
    └──────┬───────┘
           ▼
    ┌──────────────┐
    │  Module Store │
    │  Browse 60+  │
    │  modules +   │
    │  33 agents   │
    └──────┬───────┘
           ▼
    ┌──────────────┐
    │  Payment     │ ─── NowPayments (crypto) / Stripe (coming)
    └──────┬───────┘
           ▼
    ┌──────────────┐
    │  Configure   │ ─── Brand voice, knowledge base, agent settings
    │  Agents      │
    └──────┬───────┘
           ▼
    ┌──────────────┐
    │  AGENT LIVE  │ ─── First notification to client
    └──────────────┘
```

---

## 5. Multi-Tenant Data Architecture

```
PostgreSQL (production) / SQLite (dev)
│
├── Table: bredbound_businessinstance (hub app, label: bredbound)
│       id │ owner_id │ slug │ business_type │ installation_type
│       storage_used_mb │ allowed_ips │ sync_token
│
├── Table: bredbound_modulecatalog
│       id │ module_id │ category │ url_namespace │ pricing
│
├── Table: bredbound_tenantmodule (FK → BusinessInstance)
│       id │ business_id │ module_id │ tier │ config_json
│
├── Table: bredbound_businessemployee (FK → BusinessInstance)
│       id │ business_id │ user_id │ role │ access_level
│
├── Table: agents_agentcatalog (coming — Sprint A)
│       id │ slug │ role │ system_prompt │ category │ tier_required
│
├── Table: workspace_admin_hiredaiemployee (FK → BusinessInstance)
│       id │ employer_id │ tier_id │ agent_catalog_id │ tokens_used
│
├── Table: serea_conversationmessage (AI chat history)
│       id │ agent_id │ content │ role │ is_permission_request
│
└── Table: inspector_compliancecheck (append-only, immutable)
        id │ business_id │ agent_name │ decision │ log_hash │ prev_hash

Row-Level Security: Every agent query scoped to request.current_business
Audit tables: INSERT only — no UPDATE or DELETE
```

---

## 6. Security Architecture

```
INTERNET
    │
    ▼
┌─────────────────────────────┐
│  Cloudflare (Edge Layer)     │
│  WAF + DDoS + Bot Protection │
│  SSL Termination (TLS 1.3)  │
│  Rate Limiting at Edge       │
└────────────┬────────────────┘
             │
    ┌────────▼─────────────────────────────┐
    │  Nginx (reverse proxy)                │
    │  Static files served directly         │
    │  Gzip compression enabled             │
    └────────┬──────────────────────────────┘
             │
    ┌────────▼───────────────────┐
    │  Gunicorn (WSGI server)    │
    │  Django 4.2 LTS            │
    │  Inspector middleware ✅   │
    │  BusinessAccessMiddleware  │
    │  django-axes (brute-force) │
    │  django-otp (2FA)          │
    └────────┬───────────────────┘
             │ Private network only
    ┌────────▼──────────────────┐
    │  PostgreSQL                │
    │  Private IP only           │
    │  Encrypted backups         │
    └────────────────────────────┘

Auth: allauth (email + Google/Facebook/GitHub OAuth)
Admin panel: VPN + MFA (workspace subdomain only)
Secrets: django-environ (.env file, not committed)
Field encryption: django-encrypted-model-fields (Fernet) on AICredential
```

---

## 7. Hub Module Integration Flow

Agents write into existing hub modules:

```
┌──────────────────────────────────────────────────────────┐
│                    BENGALBOUND HUB                       │
│  modules/crm/  modules/hr/  modules/payroll/  ...60+     │
└──────────────────────┬───────────────────────────────────┘
                       │ ForeignKey('bredbound.BusinessInstance')
          ┌────────────┴──────────────────────────────┐
          │             AGENTS/ LAYER                  │
          │                                            │
          │  Crux ──────────────────► modules/crm/     │
          │  Lead Hunter ───────────► modules/leads/   │
          │  Hera ──────────────────► modules/hr/      │
          │  Cash ──────────────────► modules/payroll/ │
          │  Reporting Bot ─────────► modules/reports/ │
          │  Nova ──────────────────► modules/ai_analytics/ │
          │  Atlas ─────────────────► modules/task_board/  │
          │  Sage ──────────────────► modules/contracts/   │
          │                                            │
          │  ⚠️ ALL WRITES PASS THROUGH INSPECTOR FIRST│
          └────────────────────────────────────────────┘
```

---

## 8. Notification Flow

```
Event (e.g. "Agent Aria resolved a support ticket")
    │
    ▼
Django (notification logic in views)
    │
    ├── In-console notification (console_admin templates)
    ├── Email (django-allauth email backend via SMTP)
    └── Webhook to Slack (if configured in workspace_admin)

Approval flow (human-in-the-loop via Serea):
    │
    ├── ConversationMessage created with is_permission_request=True
    ├── Client sees in console and approves/denies
    │   POST /serea/permission/<id>/respond/
    └── Agent receives decision and acts accordingly
```

---

## 9. Deployment Pipeline

```
Developer pushes to dev branch
    │
    ▼
GitHub Actions triggered
    │
    ├── Lint (Black, Ruff)
    ├── Unit tests (pytest-django)
    ├── Security scan (CodeQL)
    │
    ├─── Tests FAIL → Block merge
    │
    └─── Tests PASS
              │
              ├── Render (auto-deploy on push — render.yaml)
              │     ├── pip install -r requirements.txt
              │     ├── python manage.py migrate
              │     ├── python manage.py seed_modules
              │     ├── python manage.py seed_agents
              │     └── python manage.py collectstatic --no-input
              │
              ├── Netlify (public site — netlify.toml)
              │     └── python manage.py export_static --settings=netlify_settings
              │
              └── VPS (manual deploy)
                  ├── SSH to server
                  ├── git pull
                  ├── pip install -r requirements.txt
                  ├── python manage.py migrate
                  ├── python manage.py collectstatic --no-input
                  └── systemctl restart gunicorn
```

---

## 10. VPS Infrastructure

```
INTERNET
    │
    ▼
┌─────────────────────────────────┐
│  Cloudflare                      │
└─────────────┬───────────────────┘
              │
┌─────────────▼───────────────────────────────────────┐
│  Hetzner VPS (CX42 → AX52 → AX102 as we scale)      │
│                                                      │
│  ┌─────────────┐   ┌──────────────────────────────┐  │
│  │  Nginx       │   │  Celery Worker + Beat         │  │
│  │  Port 80/443 │   │  Serea AI tasks               │  │
│  │  Reverse     │   │  (monitor/content/briefing)   │  │
│  │  proxy       │   └──────────────▲───────────────┘  │
│  └──────┬──────┘                   │                  │
│         │                   ┌──────▼──────────────┐   │
│  ┌──────▼──────────────────┐│  Redis (Celery broker)│  │
│  │  Gunicorn (Django 4.2)   │└─────────────────────┘  │
│  │  Port 8000 (internal)   │                          │
│  │  Inspector middleware ✅ │                          │
│  └──────┬──────────────────┘                          │
│         │                                             │
│  ┌──────▼──────────────────┐                          │
│  │  PostgreSQL              │                          │
│  │  Port 5432 (internal)   │                          │
│  └──────────────────────────┘                          │
│                                                      │
└─────────────────────────────────────────────────────┘

AI calls:
  Dev/Render: litellm Python library → Groq (meta-llama/llama-4-scout-17b-16e-instruct, 30k TPM free)
  VPS prod:   LiteLLM proxy at LITELLM_BASE_URL → Groq / OpenRouter / Gemini
```

### VPS Scaling Path

| Stage | Server | Specs | Cost | Clients |
|---|---|---|---|---|
| Startup | Hetzner CX42 | 8 vCPU · 16GB RAM · 160GB SSD | $19/mo | 0–50 |
| Growth | Hetzner AX52 | 12 vCPU · 64GB RAM · 512GB NVMe | $56/mo | 50–300 |
| Scale | Hetzner AX102 ×2 | 24 vCPU · 128GB RAM · 1TB NVMe | $292/mo | 300–1,000 |
| Enterprise | Hetzner GPU (RTX 4000) | GPU · 64GB · 1TB | $380/mo | 1,000+ |

---

*BengalBound HUB — Architecture v2.1 — Updated June 2026*
*Diagrams use ASCII art for universal compatibility*
