# Next Steps for Development
**Date:** June 2026 | **Branch:** `dev`

With the core backend successfully deployed to Google Cloud Run, the development team's focus shifts from foundational setup to feature completeness, API development, and technical debt reduction.

---

## 1. REST API Layer (Done)
The platform currently relies entirely on Django templates. To support future Next.js, Flutter mobile apps, or third-party integrations, we need a robust API.

- **Status:** Phase 1 complete. DRF and SimpleJWT are installed. Global routing at `/api/v1/` is set up. Core `hub` and `agents` APIs are live with JWT authentication.
- **Next:** Expand API coverage to other modules (`serea/`, `billing/`, etc.) as needed.

## 2. Stripe Billing Integration (Done)
The console previously relied on NowPayments. Standard fiat processing is now available.

- **Status:** Complete. The `billing/` app has been initialized. `BusinessSubscription` is mapped to `StripeCustomer`. Checkout sessions, customer portals, and webhook handlers have been fully implemented to handle upgrades, downgrades, and cancellations securely.

## 3. Security Enhancements (Done)
Hardening the platform against abuse and attacks.

- **Status:** Complete. We have implemented Two-Factor Authentication (TOTP) UI for user logins, configured DRF API Rate Limiting (throttling), and tuned `django-axes` alongside adding strict HTTP security headers (like `SECURE_REFERRER_POLICY`).

## 4. Test Coverage (Done)
The current test suite is thin and needs robust coverage before we scale.

- **Status:** Complete. We achieved 80%+ test coverage for `hub`, `accounts`, and `serea`. Hanging tests fixed by overriding celery behavior in eager tests using `.apply()`.

## 5. Real-time Features (WebSockets)
Serea AI chat currently relies on HTTP polling.

- **Task:** Implement Django Channels.
- **Scope:** Replace `/serea/agent/<id>/chat/` polling with a WebSocket connection for real-time streaming of AI responses. Configure a Redis channel layer.

## 6. Framework Upgrades (Done)
Stay ahead of LTS deprecation cycles.

- **Status:** Complete. Migrated to Django 5.0.x successfully and validated via `check --deploy`.
