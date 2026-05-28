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

### Week 2 — VPS & Ollama Deployment
- [ ] **Hetzner Cloud VPS Provisioning:** Hetzner CX42 instance setup ($19/mo, 8 vCPUs, 16GB RAM).
- [ ] **Install Ollama:**
  ```bash
  curl -fsSL https://ollama.ai/install.sh | sh
  systemctl enable ollama
  ollama pull mistral:7b    # 4.1GB - general chat & Serea Content
  ollama pull phi3:mini     # 2.3GB - quick classification & Inspector compliance
  ```
- [ ] **Setup Postgres Database:** Provision PostgreSQL 16 database.
- [ ] **Setup Nginx reverse proxy** and Let's Encrypt SSL certificates.

### Week 3 — Development Environment
- [ ] Distribute the **[`docs/dev/DEV_KIT.md`](file:///d:/Bengal%20bound/dev-backoffice/docs/dev/DEV_KIT.md)** to all developers.
- [ ] Implement Husky / Pre-commit hooks to block commits containing hardcoded secrets.

### Week 4 — Sprints A & B Kickoff
- [ ] Finalize task assignments for creating `agents/` and porting priority specialist models.

---

## 🛠️ Tech Stack Decisions & Fallback Matrix

*   **AI Primary Model:** Self-hosted Ollama on Hetzner VPS (`mistral:7b` + `phi3:mini`). This maintains our **98%+ Blended Gross Margins** and eliminates usage-based API billings.
*   **AI Fallback Provider:** LiteLLM routes automatically to Gemini 1.5 Flash (via `LITELLM_BASE_URL` proxy) when Ollama is offline or overloaded.
*   **Task Queue:** Celery + Redis beats for scheduling Serea agents.

### VPS Scaling Upgrades Checklist
*   **50 active clients:** Upgrade Heterzner VPS to AX52 node ($56/mo). Pull `llama3:8b` (4.7GB) or `qwen2.5:14b` (9GB) for higher reasoning capabilities.
*   **300 active clients:** Upgrade to AX102 nodes ($292/mo).
*   **1,000+ active clients:** Pull dedicated Hetzner GPU instances ($380/mo) to load `llama3:70b` models.
