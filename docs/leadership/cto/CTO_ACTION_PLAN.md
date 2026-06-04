# CTO Action Plan & Technical Roadmap
# BengalBound HUB — BengalBound Ltd
**Owner:** CTO
**Target:** September 2026 Bangladesh Launch

---

## ⚡ CTO Immediate Priorities (First 30 Days)

### Week 1 — Architecture Lock-in & Team Setup
- [ ] **Review and sign off** on `docs/leadership/cto/CTO_TECHNICAL_BRIEFING.md`.
- [ ] **Set up GitHub organisation** — create branch protection rules on `main` (require 2 approvals, CI pass).
- [ ] **Setup Linear.app** for task breakdowns and tracking.
- [ ] **Enforce Pre-commit Standards** — Black/Ruff for Python, Prettier/ESLint for frontend styles.

### Week 2 — Cloud Infrastructure ✅ DEPLOYED
- [x] **Google Cloud Run** — `bengal-bound-hub` service deployed in `us-south1`, project `serea-ai-agent-489222`
  - URL: https://bengal-bound-hub-u5i67kezxa-vp.a.run.app
  - Gunicorn on port 8080, auto-scaled, PostgreSQL via `DATABASE_URL`
  - Startup entrypoint runs: `migrate` → `seed_modules` → `seed_agents` → gunicorn
- [x] **LiteLLM proxy** at `LITELLM_BASE_URL` — routes AI calls (Gemini / OpenRouter fallback)
- [ ] **Hetzner VPS + Ollama** — planned for Phase 2 (200+ clients) to cut AI inference costs to near-zero
  ```bash
  # Phase 2 only — NOT current deployment
  ollama pull mistral:7b    # 4.1GB - general chat
  ollama pull phi3:mini     # 2.3GB - Inspector compliance
  ```

### Week 3 — Development Environment
- [ ] Distribute the **[`docs/dev/DEV_KIT.md`](file:///d:/Bengal%20bound/dev-backoffice/docs/dev/DEV_KIT.md)** to all developers.
- [ ] Implement Husky / Pre-commit hooks to block commits containing hardcoded secrets.

### Week 4 — Sprints A & B Kickoff ✅ COMPLETE
- [x] All 30 agents created in `agents/<name>/` with engine.py + tasks.py + DRF views.
- [x] Sprints A–H complete. Next: Sprint I — Veritas KYB module.

---

## 🛠️ Tech Stack Decisions & Fallback Matrix

*   **Current Deployment (Phase 0–1):** Google Cloud Run — `bengal-bound-hub` service. Django + Gunicorn on port 8080. AI via LiteLLM proxy → Gemini / OpenRouter. Zero infra management.
*   **AI Model Routing:** LiteLLM proxy at `LITELLM_BASE_URL` — all AI calls go through `agent_chat()` in `agents/utils.py`. Never call models directly.
*   **Phase 2 Plan (200+ clients):** Migrate to Hetzner VPS + self-hosted Ollama (`mistral:7b` + `phi3:mini`) to eliminate per-token API costs and achieve 98%+ gross margins.
*   **Task Queue:** Celery + Redis (currently using CELERY_TASK_ALWAYS_EAGER in dev/Cloud Run).

### VPS Scaling Plan (Phase 2+)
*   **200 clients:** Hetzner CX42 ($19/mo) + Ollama `mistral:7b`.
*   **500 active clients:** Upgrade to AX52 ($56/mo). Pull `llama3:8b` or `qwen2.5:14b`.
*   **1,000+ active clients:** AX102 ($292/mo) or GPU instances ($380/mo) + `llama3:70b`.
