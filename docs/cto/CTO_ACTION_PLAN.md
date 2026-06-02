# CTO Action Plan — BengalBound HUB
**Date:** June 2026 | **Status:** Post-Deployment Phase

The core Django backend is successfully deployed on Google Cloud Run (2GB memory, 2 CPUs) and connected to Supabase PostgreSQL. This document outlines the immediate infrastructure, security, and integration steps required to stabilize the platform for production traffic.

---

## 1. Infrastructure & CI/CD
Move away from manual CLI deployments to automated pipelines.

- [ ] **GitHub Actions CI/CD:** Set up a pipeline to automatically run tests and deploy to Google Cloud Run on merges to the `main` branch.
- [ ] **Secret Management:** Migrate environment variables from Cloud Run's plain-text env vars to **Google Cloud Secret Manager** (especially `DATABASE_URL`, `STRIPE_SECRET_KEY`, and AI API keys).
- [ ] **Redis & Celery Production Setup:** The current deployment uses synchronous execution or memory brokers. Provision a managed Redis instance (e.g., Google Cloud Memorystore or Upstash) to enable Celery Beat tasks for autonomous AI agents.

## 2. Platform Integrations
Connect the remaining microservices to the main backend.

- [ ] **LiteLLM Proxy Deployment:** Deploy the LiteLLM proxy server to route AI requests to Groq, OpenAI, and Gemini. Update `LITELLM_BASE_URL` and `LITELLM_MASTER_KEY` in Cloud Run.
- [ ] **Cloud Run Frontend Hookup:** Ensure the Cloud Run static export for the marketing site correctly builds from the `public_site` Django templates. Setup CORS and `CSRF_TRUSTED_ORIGINS` for the final custom domain.
- [ ] **Stripe Webhooks:** Once the CEO provides Stripe keys, configure the Stripe webhook endpoints and ensure they are tested against the Cloud Run URL.

## 3. Monitoring & Observability
Ensure we have visibility into production errors and performance.

- [ ] **Error Tracking:** Integrate Sentry to catch unhandled exceptions in both Django and Celery workers.
- [ ] **Cloud Run Optimization:** Monitor container startup times and memory usage. Adjust the `gunicorn` worker count and thread count to ensure the 2GB memory limit is respected while handling concurrent AI requests.

## 4. Security Hardening
Before real client data is ingested.

- [ ] **Email Verification:** Re-enable mandatory email verification in `allauth` once SMTP is configured.
- [ ] **Database Backups:** Configure Point-in-Time Recovery (PITR) and daily automated backups on the Supabase PostgreSQL instance.
