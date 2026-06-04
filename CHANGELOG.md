# Changelog

---

## [Unreleased]
### Added
- **Sprint M**: IT Officer Package Assignment & IT/Executive Command Center Dashboard.
  - Created a unified, high-fidelity **IT & Executive Command Center** page (`/workspace/control-center/`) with responsive views targeted for CTO/Dev (VPS health, telemetry metrics, and diagnostic terminal tasks), CEO (bookkeeping records, revenue aggregates, and live subscription streams), HR (staff roster list, internal office tasks), and Super Admin (platform-wide maintenance switches).
  - Implemented dynamic vanilla JS script to auto-fluctuate CPU/RAM server statistics to simulate real-time operations.
  - Implemented `control_center_vps_action` AJAX API endpoints to support live reboot, shut down, and memory compaction actions on VPS nodes, persisting state in session.
  - Added an interactive diagnostic terminal script to execute background routines (DB backups, cache flushing, agent daemons ping checks) displaying typewriter log feeds.
  - Implemented `assign_package` view in `workspace_admin/views.py` allowing IT Officers to pre-configure and assign workspace modules, custom agents, and tiers to unconfigured user accounts.
- **Sprint L**: AI Dashboard Configurator (6-question onboarding interview + custom package & budget negotiation).
  - Created `DashboardConfig` model in `hub/models.py` to persist layout, theme, color, and selected package answers.
  - Implemented `DashboardConfigurator` and `DashboardAIModifier` in `hub/dashboard_configurator.py` using `agent_chat()` with reasoning LLM to handle agent provisioning, layout generation, and natural language dashboard styling updates.
  - Enforced Veritas KYB check inside `console_admin:dashboard` view (redirecting unapproved users).
  - Created Step 7 Package Customization & Budget screen in `hybrid_onboarding.html` displaying all modules and hired agents with real-time budget calculator.
  - Integrated exchange rates to display estimates in USD or BDT depending on payment method and language preference.
  - Wired interactive Solutions Architect chatbot to dynamically update checkboxes/tiers in the cart using `<CART_UPDATE>` parsing.
  - Updated prompt to enable onboarding Solutions Architect to generate Python scripts (copy/download) for data pulling or IoT/webhook setups, step-by-step instructions, and database migrations.
- **Sprint K**: Notification Infrastructure (FCM Push, Slack Alerts, Onboarding Email Drip Campaigns).
- Added `bengalbound_core.notifications` utility for centralized dispatching.
- Added `/api/accounts/fcm-token/` endpoint and `fcm_token` to `User` model.
- Added Slack webhook alerts for new signups and successful subscription payments (Stripe & bKash).
- **New Business Verticals**: Added Driving Schools, Plumbers, Carpenters, Electricians to core `BUSINESS_TYPES`.
- **New Agents**: Created `Steer` (Driving Instructor Scheduler) and `Wrench` (Home Services Dispatcher) agents for Celery operations.
- **Sprint J**: bKash Payment Gateway integration in `billing` module.
- bKash checkout flow (initiate, callback, cancel) with tokenized API.
- Payment method selection UI (Stripe vs bKash) during Workspace plan upgrades (`billing:checkout`).

---

## [Sprint I] Veritas KYB Module & UI Polish — 2026-06-04

### 1. Veritas KYB Admin Portal
- **Created** `veritas` Django app with models: `ClientApplication`, `KYBDocument`, `SanctionsCheck`, `ClientAgreement`.
- **Created** `veritas/urls.py` and mounted to `console_admin/urls.py`.
- **Created** list and detail views for admins to review business verification applications (`kyb_list.html`, `kyb_detail.html`).
- Implemented approval and rejection workflows altering the application status.

### 2. Inspector Compliance Gate
- **Modified** `inspector/middleware.py`:
  - Added strict KYB gate: Any request to `/api/agents/` (except Veritas endpoints) is intercepted.
  - Queries `ClientApplication` for the current user and blocks access with a 403 response if status is not `approved`.

### 3. UI/UX Enhancements
- **Modified** `static/css/index.css`: Fixed a duplicate CSS block bug that was shrinking the central infinity logo and breaking the `interactive-hub-container` animation.
- **Modified** `templates/public_site/home.html`: Added a dynamic vanilla JavaScript typing effect to the hero subtitle to loop through phrases ("Built for Retail.", "Built for Agencies.", "Built for Scale.", "Run by AI Employees.").

---

## [Infra] LiteLLM Enterprise Upgrade + Dokploy Deployment — 2026-06-04

### Overview
Upgraded the LiteLLM proxy from a basic single-provider config to an enterprise-grade setup with semantic model routing, fallback chains, and Redis semantic caching. Deployed LiteLLM and Redis as managed Dokploy services on Hetzner VPS (`31.97.131.113`).

### Changes

**`litellm_config.yaml`** (root + `litellm/Dockerfile/litellm_config.yaml`)
- Rewrote from scratch with 6 semantic model aliases replacing duplicate Groq-only mappings
- Added `usage-based-routing` strategy with 3 retries and 60-second cooldowns
- Added fallback chains: Groq → OpenRouter → Gemini for all aliases
- Added Redis semantic caching (DB 2, 1-hour TTL, namespace `bengalbound:litellm`)

**`litellm/Dockerfile/Dockerfile`** (new)
- Dockerfile for building LiteLLM image in Dokploy (Build Path workaround: directory named `Dockerfile/`)

**`bengalbound_core/settings/base.py`**
- Added `LITELLM_REDIS_URL` env var (Redis DB 2 — separate from Django cache DB 1)
- Expanded `SEREA_TASK_MODELS` with `gemini` key pointing to `gemini/gemini-1.5-flash`

**`.env.example`**
- Added `LITELLM_REDIS_URL=redis://127.0.0.1:6379/2` documentation

**`.gitignore`**
- Removed `litellm_config.yaml` exclusion (file uses `os.environ/` refs, no secrets)

### Infrastructure deployed
- **Redis**: Dokploy service `bengalboundinfra-redis-itzjbq`, port 6379
- **LiteLLM**: Dokploy Docker service (`ghcr.io/berriai/litellm:main-latest`), port 4000
- **Pending**: `cloudflared` tunnel connector on VPS to reconnect `ai.neurolinkit.com` → `localhost:4000`

---

## [Sprint H] Firebase Authentication Bridge

## [Sprint H] Firebase Authentication Bridge

Allows external client surfaces (such as mobile applications or modern web frontends) to authenticate against Firebase, sync their user accounts with the Django backend, auto-provision initial workspaces, and retrieve Django Session + DRF SimpleJWT token credentials.

### 1. Database Schema Extensions
- **Modified** [accounts/models.py](file:///d:/Bengal%20bound/dev-backoffice/accounts/models.py):
  - Added `firebase_uid = models.CharField(max_length=128, unique=True, blank=True, null=True)` on the custom `User` model.
- **Created** [accounts/migrations/0005_user_firebase_uid.py](file:///d:/Bengal%20bound/dev-backoffice/accounts/migrations/0005_user_firebase_uid.py):
  - Database schema migration applying the new `firebase_uid` field.

### 2. ID Token Verification & User Synchronization
- **Modified** [accounts/views.py](file:///d:/Bengal%20bound/dev-backoffice/accounts/views.py):
  - Implemented `verify_firebase_token(id_token)`: fetches Google's public x509 cert configurations dynamically, processes signature verification using RS256, and checks issuer/audience claims.
  - Implemented `firebase_token_sync(request)`: a POST API view accepting a Firebase `id_token`. Performs account lookups (via `firebase_uid` then `email`), creates new users on the fly if needed, automatically provisions a default `BusinessInstance` + `BusinessEmployee` owner record + active `freemium` subscription, establishes the Django session, and returns simplejwt token pairs. Swapped out the deprecated `BaseUserManager.make_random_password()` password generator with modern and secure `secrets.token_urlsafe(16)` to clean up Django 5.1 deprecation warnings.
- **Modified** [accounts/urls.py](file:///d:/Bengal%20bound/dev-backoffice/accounts/urls.py):
  - Registered route `/accounts/firebase-sync/` pointing to the synchronization endpoint.

### 3. Settings Configurations
- **Modified** [bengalbound_core/settings/base.py](file:///d:/Bengal%20bound/dev-backoffice/bengalbound_core/settings/base.py):
  - Registered `FIREBASE_PROJECT_ID` parameter.
- **Modified** [bengalbound_core/settings/testing.py](file:///d:/Bengal%20bound/dev-backoffice/bengalbound_core/settings/testing.py):
  - Added `TESTING = True` to enable local mock token parsing during tests.

### 4. Automated Tests
- **Modified** [tests/test_auth.py](file:///d:/Bengal%20bound/dev-backoffice/tests/test_auth.py):
  - Added `FirebaseAuthBridgeTests` testing sync registration, email alignment mapping, UID matching logins, and invalid/empty token payloads.
  - Configured mock JWT encoding to use a 32+ character HMAC key to prevent PyJWT's `InsecureKeyLengthWarning` warning.

---

## [Sprint G] Stripe Billing Integration

Replaces the manual pricing modifications with automated Stripe Checkout flows and secure webhook event processing.

### 1. Plan Upgrade Redirects
- **Modified** [hub/views.py](file:///d:/Bengal%20bound/dev-backoffice/hub/views.py):
  - Modified the `hub_subscription` change plan action: redirects switches to paid tiers (`standard`, `premium`) to Stripe Checkout via `/billing/checkout/<plan>/?cycle=<cycle>&business_id=<id>` instead of immediately updating the local database.
- **Modified** [billing/services.py](file:///d:/Bengal%20bound/dev-backoffice/billing/services.py):
  - Corrected plan pricing calculations from `base_price_monthly` to the valid model fields `monthly_price_usd` and `annual_price_usd`.
- **Modified** [billing/views.py](file:///d:/Bengal%20bound/dev-backoffice/billing/views.py):
  - Updated checkout and portal redirection targets to resolve the company context via the `business_id` query parameter.

### 2. Premium Templates
- **Created** [templates/billing/success.html](file:///d:/Bengal%20bound/dev-backoffice/templates/billing/success.html):
  - Dark glassmorphic layout displaying a green checkout checkmark, payment details, and returns links back to the hub.
- **Created** [templates/billing/cancel.html](file:///d:/Bengal%20bound/dev-backoffice/templates/billing/cancel.html):
  - Dark glassmorphic cancel page notifying the user that payment was aborted.
- **Modified** [billing/views.py](file:///d:/Bengal%20bound/dev-backoffice/billing/views.py):
  - Set `success_view` and `cancel_view` to render the new UI templates with complete sidebar context.

### 3. Webhook Logic and SDK Corrections
- **Modified** [billing/views.py](file:///d:/Bengal%20bound/dev-backoffice/billing/views.py):
  - Wrapped Stripe SDK attributes with `getattr()` to resolve errors where `StripeObject` instances raised errors on `.get()`.
  - Parsed incoming raw payload streams (`json.loads`) to store a serialized Python dict instead of the `StripeObject` inside `BillingEvent.payload` JSONField.
  - Handled `customer.subscription.deleted` checks gracefully without throwing errors on missing subscription item configs.

### 4. Tests
- **Modified** [billing/tests.py](file:///d:/Bengal%20bound/dev-backoffice/billing/tests.py):
  - Implemented unit tests for invalid signature rejects, checkout redirects, portal redirects, and webhook updates.
- **Modified** [tests/test_hub_views.py](file:///d:/Bengal%20bound/dev-backoffice/tests/test_hub_views.py):
  - Refactored `test_hub_subscription` to verify redirect upgrades and immediate downgrades.
