<div align="center">
  <h1>BengalBound HUB — Backend Engine</h1>
  <p><strong>The Next-Generation AI-as-Employee (AIaaE) SaaS Platform</strong></p>
</div>

**BengalBound HUB** is an enterprise-grade Django 4.2 LTS multi-tenant SaaS operating system. It provides 80+ pluggable business modules, a marketplace of 30 autonomous AI Employees, and fully subdomain-routed admin surfaces—all backed by LiteLLM for dynamic, model-agnostic AI routing.

---

## 🚀 Core Architecture & Tech Stack

| Layer | Technology |
|-------|-----------|
| **Core Framework** | Django 4.2 LTS (Robust, secure, and highly scalable) |
| **Authentication** | `django-allauth` (Email + Google / Facebook / GitHub OAuth) |
| **AI Gateway** | LiteLLM Proxy (Model-agnostic routing for Gemini, OpenAI, Claude) |
| **Task Queue** | Celery + Redis (85+ scheduled autonomous business tasks) |
| **Database** | SQLite (Development) / PostgreSQL (Production) |
| **API Layer** | Django REST Framework (DRF) — Independent ViewSets per AI agent |
| **Security** | `django-axes`, `django-otp` (TOTP 2FA), `django-simple-history`, `django-encrypted-model-fields` |
| **Telephony** | Twilio, Google Voice (Voice Receptionist autonomous routing) |

---

## 🧠 Autonomous AI Fleet & Legal Compliance

BengalBound HUB features 30 distinct AI Employees. Each agent possesses autonomous internet capabilities powered by our proprietary **Universal Agent Toolkit**. 

### The Universal Toolkit
All 30 AI agents have native capabilities to perform real-time internet tasks:
- **`search_web`**: Autonomous Google/DuckDuckGo indexing for real-time information.
- **`scrape_website`**: Deep HTML text extraction for SEO audits and competitor research.
- **`call_api`**: Unauthenticated REST API integration for dynamic third-party data fetching.

### Strict International Legal Compliance
Our agents are legally insulated and ethically bound by the strict protocols of the **EU AI Act**, **GDPR**, and **US CFAA**:
1. **Machine-Readable Exclusion**: Full adherence to `robots.txt` via `urllib.robotparser`. If an AI bot is blocked, our agents will mathematically refuse to scrape the domain.
2. **Transparent Identity**: All HTTP requests are explicitly identified as `BengalBoundBot/1.0 (+https://bengalbound.com/bot-policy)`. No browser spoofing.
3. **Infrastructure Politeness**: Strict `time.sleep()` delays are enforced on targets with `Crawl-Delay` parameters to prevent DDoS-like server loads.
4. **Automated PII Stripping (GDPR)**: Built-in Regex NLP aggressively removes Personally Identifiable Information (Emails & Phone Numbers) before the scraped data enters our LLM context windows.

---

## 📂 Project Structure

```text
bengalbound_core/          # Django project root (settings, celery beat)
hub/                       # Core tenant engine (BusinessInstance, Middleware)
agents/                    # 30 AI Employee sub-apps (Autonomous brains & APIs)
   utils.py                # Universal toolkit entry point (agent_chat)
   content_strategist/     # Content creation AI agent
   oracle/                 # SEO Specialist AI agent
   scout/                  # Competitor Intelligence AI agent
   lead_hunter/            # B2B Prospecting AI agent
   ...
modules/                   # 80+ optional business domain apps (CRM, HR, POS, etc.)
serea/                     # Platform layer (Webhooks, Meta/Facebook routing)
accounts/                  # Custom Auth User models
console_admin/             # Client-facing SaaS console
public_site/               # Marketing and public landing pages
```

---

## 🛠 Quick Start (Local Development)

### 1. Environment Setup
```bash
git clone -b dev https://github.com/Adre-melech/BengalBound.git
cd BengalBound
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration & Seeding
```bash
cp .env.example .env
# Edit .env and populate SECRET_KEY and LITELLM_BASE_URL
python manage.py migrate
python manage.py seed_modules        # Populates 80+ SaaS modules
python manage.py seed_agents         # Populates 30 AI Employees
python manage.py createsuperuser
```

### 3. Start the Engine
```bash
python manage.py runserver 0.0.0.0:1234
```
> **Note:** Port `1234` is required for local testing due to `CSRF_TRUSTED_ORIGINS`.

---

## 🛡 Security & Best Practices

- **ISO/IEC 27001 & NIST SP 800-218**: Automated environment separation (`testing.py`, `.env.*`).
- **Zero-Trust Access**: `BusinessAccessMiddleware` enforces IP-locking and strict slug routing.
- **Model Encryption**: API keys and Webhook tokens are securely encrypted via Fernet encryption.

## 🤝 Contributing
1. Always branch from `dev`.
2. Ensure you run `seed_modules` and `seed_agents` after migrating.
3. Open a Pull Request against `dev`. Direct pushes to `main` are restricted.

<div align="center">
  <sub>Built with precision by the BengalBound Engineering Team.</sub>
</div>
