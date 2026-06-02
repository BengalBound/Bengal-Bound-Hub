# Next Steps for Development
**Date:** June 2026 | **Branch:** `dev`

With the core backend successfully deployed to Google Cloud Run, the development team's focus shifts from foundational setup to feature completeness, API development, and technical debt reduction.

---

## 1. REST API Layer (Done)
The platform currently relies entirely on Django templates. To support future Next.js, Flutter mobile apps, or third-party integrations, we need a robust API.

- **Status:** Phase 1 complete. DRF and SimpleJWT are installed. Global routing at `/api/v1/` is set up. Core `hub` and `agents` APIs are live with JWT authentication.
- **Next:** Expand API coverage to other modules (`serea/`, `billing/`, etc.) as needed.

## 2. Stripe Billing Integration (High Priority)
The current console relies on NowPayments. We need standard fiat processing.

- **Task:** Implement the `billing/` app with Stripe Checkout and Customer Portal.
- **Scope:** Map `HubPlanConfig` pricing directly to Stripe Products and Prices. Handle webhook events for subscription upgrades, downgrades, and cancellations.

## 3. Test Coverage
The current test suite is thin and needs robust coverage before we scale.

- **Task:** Increase test coverage to 80% on core components (`hub/`, `accounts/`, `serea/`).
- **Tools:** Integrate `pytest-django` and `factory_boy` for mock data generation.
- **Focus:** Test `BusinessAccessMiddleware` thoroughly, ensure AI tools are mocked, and validate Celery task execution.

## 4. Real-time Features (WebSockets)
Serea AI chat currently relies on HTTP polling.

- **Task:** Implement Django Channels.
- **Scope:** Replace `/serea/agent/<id>/chat/` polling with a WebSocket connection for real-time streaming of AI responses. Configure a Redis channel layer.

## 5. Framework Upgrades
Stay ahead of LTS deprecation cycles.

- **Task:** Plan migration from Django 4.2 LTS to Django 5.x.
- **Scope:** Audit existing third-party packages for Django 5 compatibility. Upgrade Python requirement if necessary.
