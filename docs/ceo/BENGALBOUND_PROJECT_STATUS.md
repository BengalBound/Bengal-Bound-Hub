# BengalBound HUB — Project Status & Work Plan
**Date:** 2026-06-04 | **Branch:** `dev` | **Last commit:** `3c8f4f1`
**Overall completion toward MVP launch: ~92%**

---

## 1. Project Identity

**BengalBound HUB** is a Django 4.2 LTS multi-tenant SaaS business operating system and AI-as-Employee marketplace. Businesses hire autonomous AI agents that hold actual job roles, complete real tasks, and report 24/7 — supervised by Inspector, an always-on compliance watchdog enforcing 40+ global laws.

**Vision:** $10M ARR by 2030. Bangladesh launch September 2026. First market: BD + SE Asia SMEs.
**Company:** BengalBound Ltd / NeurolinkIT | **CEO target:** 1,000 clients by end of 2027.

**Domains (both being purchased):**
| Domain | Purpose |
|--------|---------|
| `bengalbound.com` | Primary — marketing site, client console, customer-facing |
| `bengalbound.io` | Secondary — API/developer portal, technical subdomains |

Subdomains on `.com`: `console.bengalbound.com`, `workspace.bengalbound.com`, `app.bengalbound.com`
Subdomains on `.io`: `api.bengalbound.io`, `docs.bengalbound.io`, `status.bengalbound.io`

---

## 2. Live System

| Property | Value |
|----------|-------|
| Cloud Run service | `bengal-bound-hub` |
| Project | `serea-ai-agent-489222` |
| Region | `us-south1` |
| URL | https://bengal-bound-hub-u5i67kezxa-vp.a.run.app |
| Status | ✅ Healthy |
| Workers | Gunicorn, 3 sync workers, port 8080 |
| DB | PostgreSQL via `DATABASE_URL` (Cloud Run) / SQLite (local dev) |
| Startup | `migrate → seed_modules → seed_agents → gunicorn` |
| Tests | 776 passing, 0 failures, 6 skipped |

---

## 3. Technology Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 4.2 LTS |
| Auth | django-allauth (email + Google/Facebook/GitHub), Firebase bridge |
| Security | django-axes (brute force), django-otp (TOTP 2FA), django-simple-history |
| AI | LiteLLM proxy at `LITELLM_BASE_URL` — all calls via `agents/utils.py:agent_chat()` |
| Task queue | Celery + Redis (CELERY_TASK_ALWAYS_EAGER in dev/Cloud Run) |
| Real-time | Django Channels + WebSocket (ASGI via Daphne) |
| API | Django REST Framework + SimpleJWT + drf-spectacular |
| Payments | Stripe (global) — bKash planned Sprint J |
| Database | SQLite (dev) → PostgreSQL 16 (production via DATABASE_URL) |
| Deployment | Google Cloud Run (Phase 0–1) → Hetzner VPS + Ollama (Phase 2, 200+ clients) |
| Templates | Django templates (DRF API layer complete) |

---

## 4. Architecture

```
Public Site (bengalbound.com)
        │
        ▼
Console (console.bengalbound.com)  ←→  Workspace (workspace.bengalbound.com)
        │                                       │
        ▼                                       ▼
   Django REST API (api/v1/)
        │
        ▼
   INSPECTOR (always-on compliance gate — every mutating request)
        │
        ▼
   LiteLLM proxy (LITELLM_BASE_URL) → Gemini / OpenRouter / Ollama (Phase 2)
        │
        ▼
   30 Agent Apps (agents/<name>/engine.py + tasks.py)
        │
        ▼
   84 Business Modules (modules/<name>/)
        │
        ▼
   PostgreSQL 16 + Cloud Storage
```

**Key architectural rules:**
- App label for `hub/` is `bredbound` — all FKs use `'bredbound.BusinessInstance'`
- All AI calls go through `agents/utils.py:agent_chat()` — never call models directly
- Inspector middleware intercepts ALL POST/PUT/PATCH/DELETE requests
- Dev server runs on port 1234 only

---

## 5. Current Completion: ~92% toward MVP

| Area | % | Status |
|------|---|--------|
| Core infrastructure | 98% | ✅ Django, Channels, Celery, multi-tenant, subdomain routing, Cloud Run, LiteLLM/Redis Dokploy stack |
| Authentication & Security | 90% | ✅ Email, OAuth, OTP, TOTP 2FA, SSO, Firebase bridge |
| AI Agent system | 95% | ✅ 33 agent sub-apps, engine.py + tasks.py, DRF APIs, HiredAIEmployee, IT package assignment, skip onboarding |
| Inspector compliance | 90% | ✅ Middleware, 40+ rules, immutable audit log, Slack/PagerDuty alerts |
| Billing | 95% | ✅ Stripe checkout, webhooks, subscriptions, bKash payment gateway |
| Client onboarding | 95% | ✅ Signup, OTP verify, Veritas KYB, TOS/DPA/AUP signing, AI setup interview configurator |
| Business modules | 95% | ✅ 84 modules seeded, DRF APIs, templates |
| Notifications | 90% | ✅ Central notification routing, FCM push, Slack alerts, Day 1/3/7/30 onboarding sequences |
| Marketing/SEO | 70% | ✅ Public site, blog, FAQ, pricing, pre-account budget negotiator |
| Deployment/DevOps | 90% | ✅ Cloud Run live, Hetzner LiteLLM service, Redis cache backend |

---

## 6. Sprint History (Complete)

| Sprint | What | Commits |
|--------|------|---------|
| A | AgentCatalog model + 30 agents seeded via `seed_agents` | `3007d8c` |
| B | 33 agent sub-apps — `engine.py` + `tasks.py` per agent | — |
| C | `agents/utils.py` + `CELERY_BEAT_SCHEDULE` for all agents | — |
| D | DRF ViewSets, serializers, urls per agent | — |
| E | Agent test coverage (`tests/test_agent_sprint_e.py`) | `dc3ab3e` |
| F | Real-time WebSocket permission resolution | `eb4552d` |
| G | Stripe billing: checkout, webhooks, success/cancel pages | `1b6211b` |
| H | Firebase auth bridge: `firebase_token_sync()`, `firebase_uid` on User | `1b6211b` |
| I | Veritas KYB Compliance module & digitally signed agreements | `ed0fc3e` |
| J | bKash tokenized payment gateway integration | `3c8f4f1` |
| K | FCM push, Slack alerts, Day 1/3/7/30 onboarding sequences | `3c8f4f1` |
| L | AI Onboarding interview & dynamic package budget configurator | `3c8f4f1` |
| M | IT Package Assignment & IT/Executive Control Center Dashboard | `3c8f4f1` |
| N | Onboarding Skip Booking & Pre-Account Negotiator | `84b8158` |
| Fixes | Bug fixes + full doc alignment (this session) | `84b8158` |

**Bugs fixed in last session (2026-06-03):**
1. `inspector/views.py` — `return True` → `return "approved"` in no-rules path
2. `hub/api_views.py` — `businessemployee__user` → `employees__user` (wrong FK reverse name)
3. `hub/tests.py` — URL namespaces corrected to `api:hub_api:*` and `api:agents_global_api:*`
4. `modules/factory_ops/tests.py` — `BusinessInstance` created without `owner` (NOT NULL crash)
5. `accounts/views.py` + `development.py` — Firebase test tokens now work with `TESTING=True`

---

## 7. Launch Blockers (Must Fix Before First Paying Client)

All primary launch blockers are now resolved. Remaining tasks involve scale operations, load testing, and marketing setups.

---

## 8. Sprint I — Veritas KYB (NEXT — Start Now)

**Spec:** `docs/platform/veritas_client_kyb_onboarding.md`
**Goal:** Build the client onboarding gate. Before any AI agent activates, every client must pass KYB verification and sign four legal agreements.

### 8.1 New App: `veritas/`

```
veritas/
  __init__.py
  apps.py           ← AppConfig name = 'veritas'
  models.py         ← ClientApplication, KYBDocument, SanctionsCheck, ClientAgreement
  views.py          ← DRF ViewSets for apply, document upload, status, signing
  serializers.py
  urls.py           ← app_name = 'veritas'
  tasks.py          ← Celery: registry_check, sanctions_scan, risk_score_calculate
  engine.py         ← AI-powered OCR + risk analysis via agent_chat()
  migrations/
  management/
    commands/
      seed_kyb_rules.py   ← seed risk scoring rules
```

### 8.2 Models

```python
# ClientApplication — the KYB record per business
class ClientApplication(models.Model):
    STATUS = [
        ('submitted', 'Submitted'),
        ('documents_pending', 'Documents Pending'),
        ('under_review', 'Under Review — AI'),
        ('human_review', 'Human Review Required'),
        ('approved', 'Approved'),        # Green — agents activate
        ('rejected', 'Rejected'),        # Red — permanent block
        ('suspended', 'Suspended'),
    ]
    RISK_LEVEL = [('green', 'Green'), ('amber', 'Amber'), ('red', 'Red')]

    business             = models.OneToOneField('bredbound.BusinessInstance', on_delete=models.CASCADE)
    user                 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company_legal_name   = models.CharField(max_length=500)
    registration_number  = models.CharField(max_length=200)
    jurisdiction         = models.CharField(max_length=100)
    registered_address   = models.TextField()
    incorporation_date   = models.DateField(null=True)
    business_type        = models.CharField(max_length=200)
    website              = models.URLField(blank=True)
    director_name        = models.CharField(max_length=300)
    director_email       = models.EmailField()
    # Verification results
    registry_verified    = models.BooleanField(null=True)
    sanctions_clear      = models.BooleanField(null=True)
    documents_verified   = models.BooleanField(null=True)
    risk_score           = models.IntegerField(null=True)        # 0–100
    risk_level           = models.CharField(max_length=10, choices=RISK_LEVEL, blank=True)
    ai_risk_summary      = models.TextField(blank=True)
    status               = models.CharField(max_length=30, choices=STATUS, default='submitted')
    rejection_reason     = models.TextField(blank=True)
    approved_at          = models.DateTimeField(null=True)
    submitted_at         = models.DateTimeField(auto_now_add=True)
    next_review_date     = models.DateField(null=True)           # Quarterly re-check

# KYBDocument — uploaded verification docs
class KYBDocument(models.Model):
    DOC_TYPES = [
        ('incorporation', 'Certificate of Incorporation'),
        ('trade_license', 'Trade License'),
        ('vat_cert', 'VAT/Tax Certificate'),
        ('proof_address', 'Proof of Business Address'),
        ('director_id', 'Director National ID / Passport'),
        ('bank_statement', 'Bank Statement Header'),
    ]
    application      = models.ForeignKey(ClientApplication, on_delete=models.CASCADE)
    document_type    = models.CharField(max_length=30, choices=DOC_TYPES)
    file             = models.FileField(upload_to='kyb/documents/')
    ocr_extracted    = models.JSONField(default=dict)    # AI-extracted fields
    ai_verified      = models.BooleanField(null=True)
    rejection_reason = models.TextField(blank=True)
    status           = models.CharField(max_length=20, default='pending')
    uploaded_at      = models.DateTimeField(auto_now_add=True)

# ClientAgreement — digital signatures on legal docs
class ClientAgreement(models.Model):
    DOC_TYPES = [
        ('tos', 'Terms of Service'),
        ('dpa', 'Data Processing Agreement'),
        ('aup', 'Acceptable Use Policy'),
        ('ai_ethics', 'AI Ethics Acknowledgement'),
    ]
    application    = models.ForeignKey(ClientApplication, on_delete=models.CASCADE)
    agreement_type = models.CharField(max_length=20, choices=DOC_TYPES)
    version        = models.CharField(max_length=20)
    signed         = models.BooleanField(default=False)
    signed_at      = models.DateTimeField(null=True)
    ip_address     = models.GenericIPAddressField(null=True)
    signature_hash = models.CharField(max_length=64)   # SHA-256 of content + timestamp

# SanctionsCheck — OFAC/UN/EU/FATF screening result
class SanctionsCheck(models.Model):
    application    = models.ForeignKey(ClientApplication, on_delete=models.CASCADE)
    checked_entity = models.CharField(max_length=500)
    list_checked   = models.CharField(max_length=100)  # 'OFAC', 'UN', 'EU', 'FATF'
    match_found    = models.BooleanField(default=False)
    match_score    = models.FloatField(null=True)
    checked_at     = models.DateTimeField(auto_now_add=True)
```

### 8.3 API Endpoints (`/api/v1/kyb/`)

| Method | Endpoint | Action |
|--------|----------|--------|
| `POST` | `/apply/` | Submit company details, create ClientApplication |
| `POST` | `/apply/{id}/documents/` | Upload KYB documents |
| `GET`  | `/apply/{id}/status/` | Check application status + risk score |
| `POST` | `/apply/{id}/sign/{doc_type}/` | Digital sign TOS / DPA / AUP / AI Ethics |
| `GET`  | `/applications/` | NeurolinkIT ops: list all applications |
| `PATCH`| `/applications/{id}/approve/` | Manual approval (Amber cases) |
| `PATCH`| `/applications/{id}/reject/` | Manual rejection with reason |
| `POST` | `/applications/{id}/rescan/` | Re-run AI risk analysis |

### 8.4 engine.py — AI Risk Analysis

```python
# veritas/engine.py
from agents.utils import agent_chat

SYSTEM_PROMPT = """
You are Veritas — BengalBound's KYB compliance agent.
Analyze business registration documents and return a JSON risk assessment.
Always respond with valid JSON only:
{
  "risk_score": 0-100,
  "risk_level": "green" | "amber" | "red",
  "registry_verified": true | false,
  "sanctions_clear": true | false,
  "documents_verified": true | false,
  "summary": "one-paragraph risk summary",
  "red_flags": ["list of specific concerns"]
}
Green (0-30): auto-approve. Amber (31-60): human review. Red (61-100): reject.
"""

def analyze_application(application) -> dict:
    docs_summary = _summarize_documents(application)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Company: {application.company_legal_name}\n"
                                     f"Jurisdiction: {application.jurisdiction}\n"
                                     f"Documents: {docs_summary}"}
    ]
    raw = agent_chat(messages)
    return json.loads(raw)
```

### 8.5 Inspector Gate Integration

After Veritas is built, add this check to the Agent activation flow:

```python
# workspace_admin/views.py — when client tries to hire/activate an agent
from veritas.models import ClientApplication

def hire_agent(request, slug):
    business = get_object_or_404(BusinessInstance, slug=slug)
    kyb = ClientApplication.objects.filter(business=business).first()
    if not kyb or kyb.status != 'approved':
        return Response(
            {"error": "KYB verification required before hiring AI agents."},
            status=403
        )
    # proceed with hiring...
```

### 8.6 Tasks

```python
# veritas/tasks.py
@shared_task
def run_kyb_analysis(application_id):
    """Async AI risk analysis — triggered after document upload."""
    app = ClientApplication.objects.get(id=application_id)
    result = analyze_application(app)
    app.risk_score = result['risk_score']
    app.risk_level = result['risk_level']
    app.ai_risk_summary = result['summary']
    if result['risk_level'] == 'green':
        app.status = 'approved'
        app.approved_at = timezone.now()
    elif result['risk_level'] == 'amber':
        app.status = 'human_review'
    else:
        app.status = 'rejected'
        app.rejection_reason = ', '.join(result.get('red_flags', []))
    app.save()

@shared_task
def quarterly_reverification():
    """Re-verify all approved clients every 90 days."""
    due = ClientApplication.objects.filter(
        status='approved',
        next_review_date__lte=timezone.now().date()
    )
    for app in due:
        run_kyb_analysis.delay(app.id)
```

### 8.7 Settings & URLs

```python
# bengalbound_core/settings/base.py — add to INSTALLED_APPS
'veritas',

# bengalbound_core/api_urls.py — add to urlpatterns
path('kyb/', include('veritas.urls')),

# bengalbound_core/workspace_urls.py — add
path('<slug:slug>/kyb/', include('veritas.workspace_urls')),
```

### 8.8 Delivery Phases

| Phase | Scope | Weeks |
|-------|-------|-------|
| Phase 1 | Application form, document upload, AI OCR via agent_chat(), manual review, agreement signing | 1–2 |
| Phase 2 | OpenSanctions screening, risk score auto-approve/reject, inspector gate integration | 3–4 |
| Phase 3 | Quarterly re-monitoring, adverse media scan, license expiry alerts | 5–6 |

**Start with Phase 1 — it unblocks everything.**

---

## 9. Sprint J — bKash Payment (After Sprint I)

**Goal:** Add bKash (Bangladesh's primary mobile payment) as a payment gateway alongside Stripe.

### 9.1 Why Critical
- 95%+ of Bangladesh's digital payment market
- Target customer base (BD SMEs) cannot pay by international card
- Without bKash, the entire BD go-to-market is blocked

### 9.2 Approach

```python
# billing/bkash_service.py
import requests
from django.conf import settings

class BKashService:
    """bKash Payment Gateway Integration"""
    BASE_URL = settings.BKASH_BASE_URL  # 'https://tokenized.pay.bka.sh/v1.2.0-beta'

    def create_payment(self, amount: float, invoice_id: str) -> dict:
        """Create a bKash payment request."""
        token = self._get_token()
        resp = requests.post(
            f"{self.BASE_URL}/tokenized/checkout/create",
            headers={"Authorization": token, "X-APP-Key": settings.BKASH_APP_KEY},
            json={
                "mode": "0011",
                "payerReference": invoice_id,
                "callbackURL": f"{settings.SITE_URL}/billing/bkash/callback/",
                "amount": str(amount),
                "currency": "BDT",
                "intent": "sale",
                "merchantInvoiceNumber": invoice_id,
            }
        )
        return resp.json()

    def execute_payment(self, payment_id: str) -> dict:
        """Execute a payment after user confirmation."""
        token = self._get_token()
        resp = requests.post(
            f"{self.BASE_URL}/tokenized/checkout/execute",
            headers={"Authorization": token, "X-APP-Key": settings.BKASH_APP_KEY},
            json={"paymentID": payment_id}
        )
        return resp.json()
```

### 9.3 Required Env Variables

```
BKASH_APP_KEY=
BKASH_APP_SECRET=
BKASH_USERNAME=
BKASH_PASSWORD=
BKASH_BASE_URL=https://tokenized.pay.bka.sh/v1.2.0-beta
```

### 9.4 New URL Routes

```python
# billing/urls.py — add
path('bkash/initiate/', views.bkash_initiate, name='bkash_initiate'),
path('bkash/callback/', views.bkash_callback, name='bkash_callback'),
path('bkash/cancel/', views.bkash_cancel, name='bkash_cancel'),
```

---

## 10. Sprint K — Onboarding & Notification Infrastructure

### 10.1 Email Sequences (Day 1 / 3 / 7 / 30)

```python
# accounts/tasks.py
@shared_task
def send_onboarding_sequence(user_id: int, day: int):
    """Send onboarding email at Day 1, 3, 7, 30 after registration."""
    user = User.objects.get(id=user_id)
    templates = {
        1: 'emails/onboarding_day1.html',   # Welcome + quickstart
        3: 'emails/onboarding_day3.html',   # "Have you set up your first agent?"
        7: 'emails/onboarding_day7.html',   # Tips + feature spotlight
        30: 'emails/onboarding_day30.html', # "Upgrade to unlock more agents"
    }
    send_mail(
        subject=...,
        html_message=render_to_string(templates[day], {'user': user}),
        recipient_list=[user.email],
    )
```

### 10.2 FCM Push Notifications

```python
# Required: google-firebase-admin package
# accounts/push_service.py
import firebase_admin.messaging as fcm

def send_push(token: str, title: str, body: str):
    message = fcm.Message(
        notification=fcm.Notification(title=title, body=body),
        token=token,
    )
    fcm.send(message)
```

### 10.3 Slack/PagerDuty Security Alerts (Inspector)

```python
# inspector/alerts.py
import requests
from django.conf import settings

def alert_security_incident(incident):
    if settings.SLACK_WEBHOOK_URL:
        requests.post(settings.SLACK_WEBHOOK_URL, json={
            "text": f"🚨 *BengalBound Security Incident*\n"
                    f"Severity: {incident.severity.upper()}\n"
                    f"Root cause: {incident.root_cause[:200]}\n"
                    f"Business: {incident.compliance_check.business}"
        })
```

---

## 11. Sprint L — AI Dashboard Configurator

**Spec:** `docs/architecture/CLIENT_DASHBOARD_AI.md`

The 6-question AI onboarding interview that builds each client's perfect workspace in 3 minutes. After KYB passes, clients answer 6 questions → AI configures agents + dashboard layout automatically.

```python
# hub/dashboard_configurator.py
class DashboardConfigurator:
    BUSINESS_AGENT_MAP = {
        "ecommerce":     ["merch", "concierge", "serea-content", "flux"],
        "agency":        ["lead_hunter", "content_architect", "oracle", "reporting_bot"],
        "clinic":        ["medibook", "concierge", "hera", "sage"],
        "restaurant":    ["concierge", "serea-content", "cash", "tempo"],
        "real_estate":   ["realt", "concierge", "lead_hunter", "sage"],
        "consulting":    ["lead_hunter", "atlas", "reporting_bot", "sage"],
        "manufacturing": ["payload", "flux", "hera", "atlas"],
    }

    def configure(self, business, answers: dict):
        agents = self.BUSINESS_AGENT_MAP.get(answers['business_type'], [])
        # AI generates personalised layout via agent_chat()
        ...
```

---

## 12. Sprint M+ — Phase 2 Infrastructure

| Item | Description |
|------|-------------|
| Hetzner VPS + Ollama | Move AI inference in-house at 200+ clients for 98%+ gross margins |
| PostgreSQL read replicas | For 1,000+ clients |
| Cloudflare WAF | Edge-level DDoS + bot protection |
| Redis production | Replace CELERY_TASK_ALWAYS_EAGER with real Redis broker |
| SSL auto-renewal | Let's Encrypt via Cloudflare on custom domain |
| WhatsApp Business API | Concierge agent integration for BD market |
| ISO 27001 | Compliance certification (2028 target) |
| SOC 2 Type II | Enterprise compliance (2028 target) |

---

## 13. Management Commands Reference

```bash
python manage.py runserver 0.0.0.0:1234   # Dev server (port 1234 always)
python manage.py migrate
python manage.py seed_modules              # 84 business modules
python manage.py seed_agents               # 30 AI agent catalog entries
python manage.py seed_compliance_rules     # 40+ Inspector compliance rules
python manage.py createsuperuser
python manage.py collectstatic             # Production only
python manage.py test --settings=bengalbound_core.settings.development
```

---

## 14. Key File Locations

| Purpose | File |
|---------|------|
| INSTALLED_APPS + MIDDLEWARE | `bengalbound_core/settings/base.py` |
| Dev overrides (DEBUG=True, TESTING=True) | `bengalbound_core/settings/development.py` |
| Production (Cloud Run) | `bengalbound_core/settings/production.py` |
| Test settings | `bengalbound_core/settings/testing.py` |
| Root URL conf | `bengalbound_core/urls.py` |
| API v1 URLs | `bengalbound_core/api_urls.py` |
| Workspace URLs | `bengalbound_core/workspace_urls.py` |
| Business middleware | `hub/middleware.py` |
| Inspector middleware | `inspector/middleware.py` |
| AI utility | `agents/utils.py` — `agent_chat()` |
| Inspector compliance gate | `inspector/views.py` — `run_compliance_evaluation()` |
| Stripe billing | `billing/views.py`, `billing/services.py` |
| Firebase auth | `accounts/views.py` — `firebase_token_sync()` |
| Hub DRF API | `hub/api_views.py`, `hub/api_urls.py` (namespace: `api:hub_api`) |
| Agent catalog API | `agents/global_api_urls.py` (namespace: `api:agents_global_api`) |
| Agent API (generic) | `agents/api_views.py` |
| Console admin | `console_admin/views.py`, `console_admin/views_agents.py` |
| Agent hiring | `workspace_admin/models.py:HiredAIEmployee` |
| Module seeder | `hub/management/commands/seed_modules.py` |
| Agent seeder | `agents/management/commands/seed_agents.py` |
| Compliance seeder | `inspector/management/commands/seed_compliance_rules.py` |

---

## 15. Git Remotes — Push ALL Three After Every Commit

```bash
git push origin dev      # https://github.com/Adre-melech/BengalBound.git
git push newhub dev      # https://github.com/BengalBound/Bengal-Bound-Hub.git
git push showcase dev    # https://github.com/shadman1996/BengalBoundHub.git
```

---

## 16. DO NOT Rules

- Call AI models directly — use `agent_chat()` from `agents/utils.py` only
- Use `'hub.BusinessInstance'` as FK target — always use `'bredbound.BusinessInstance'`
- Edit files in `d:\Bengal bound\Bengal Bound.worktrees\agents-constitutional-fox\` (read-only source)
- Run on any port other than 1234 in dev
- Skip `TESTING=True` bypass in production — it must be False in `production.py`
- Add secrets to `base.py` — use environment variables only

---

## 17. Full Sprint Roadmap

| Sprint | Work | Priority | Est. Effort | Status |
|--------|------|----------|-------------|--------|
| **I** | **Veritas KYB** — Phase 1 (forms, upload, AI review, agreements) | 🔴 Critical | 2–3 weeks | ✅ Done |
| **I continued** | Veritas Phase 2 (sanctions screening, auto-approve/reject, inspector gate) | 🔴 Critical | 2 weeks | ✅ Done |
| **J** | bKash payment gateway | 🔴 Critical | 1–2 weeks | ✅ Done |
| **K** | Onboarding emails (Day 1/3/7/30) + FCM push + Slack/PagerDuty alerts | 🟠 High | 1–2 weeks | ✅ Done |
| **L** | AI Dashboard Configurator (6-question onboarding interview) | 🟠 High | 2 weeks | ✅ Done |
| **M** | Compliance dashboard UI (IT/Executive Center, Package Assignment) | 🟡 Medium | 1 week | ✅ Done |
| **N** | Onboarding Skip Booking & Pre-Account Negotiator | 🔴 Critical | 1 week | ✅ Done |
| **O** | WhatsApp integration (Concierge agent) | 🟡 Medium | 2 weeks | 📅 Upcoming |
| **P** | Redis in production + Hetzner VPS + Ollama (200+ clients) | 🟡 Medium (Phase 2) | 1 week | 📅 Upcoming |
| **Q** | AppSumo LTD listing preparation | 🟡 Medium | 1 week | 📅 Upcoming |
| **R** | Multi-language support (Bengali, Arabic, Hindi) | 🟢 Low | 2 weeks | 📅 Upcoming |
| **S** | Mobile app (deferred) | 🟢 Future | — | 📅 Deferred |

**Target for first 10 paying clients:** Sprints I + J done (✅ Complete).
**Target for AppSumo launch:** Sprints I through L done (✅ Complete).
**Target for September 2026 Bangladesh launch:** Sprints I through N done (✅ Complete).

---

*BengalBound HUB — Living Project Document*
*Last updated: 2026-06-04 | Maintained by: Claude Code + NeurolinkIT team*
