# Antigravity Operating Guidelines
# Core System Prompting & Rules

---

## 1. Purpose
This folder serves as the central brain for **Antigravity** (AI coding assistant) when working on the BengalBound HUB codebase and documentation. It contains persistent rules, architectural constraints, and project history to ensure context is never lost between sessions.

---

## 2. Core Directives for Antigravity

### Development Philosophy
*   **Light, Easy, Powerful:** The user experience is paramount. We are building the "Apple of SaaS business operating systems."
*   **Next-Level Aesthetics:** The UI must wow the user immediately. Use modern, dynamic, and premium design systems (Outfit and Inter typography, sleek dark modes, harmony gradients).
*   **Absolute Automation:** If a human can do it, an AI should do it. Manual processes are bugs.

### Technical Mandates
*   **Backend:** Django 4.2 LTS, DRF, SQLite (dev) / PostgreSQL (production via `DATABASE_URL`).
*   **Frontend:** Django templates with rich CSS styling (Framer-like micro-interactions, responsive grids).
*   **AI Stack:** LiteLLM proxy at `LITELLM_BASE_URL` routing to Groq, OpenRouter, or Gemini. Direct model calls are strictly prohibited.
*   **Security:** Zero-trust architecture. All mutating actions must pass through the `Inspector` watchdog compliance middleware.

---

## 3. Task Execution Rules
1.  **Always Check the Architecture:** Review `docs/leadership/cto/` and `docs/tech/` before writing backend schemas.
2.  **App Label Safety:** Keep the `hub/` folder bound strictly to the `bredbound` app label; all dynamic module ForeignKeys target `'bredbound.BusinessInstance'`.
3.  **Clean Logs:** Log major architectural decisions and keep the document indices up to date.
