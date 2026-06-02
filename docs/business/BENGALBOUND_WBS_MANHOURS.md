# Work Breakdown Structure (WBS) + Man-Hours Estimation
# Bengal Bound Platform — NeurolinkIT
**Version:** 1.0 | **Date:** April 2026 | **Currency:** USD + BDT
**Classification:** Investor & Management Reference

---

## Summary Budget

| Phase | Duration | Dev Hours | Cost (BD Rate $15/hr) | Cost (Intl Rate $50/hr) |
|---|---|---|---|---|
| Phase 0 — Foundation | 4 weeks | 220 hrs | $3,300 | $11,000 |
| Phase 1 — MVP | 8 weeks | 380 hrs | $5,700 | $19,000 |
| Phase 2 — Core Agents | 12 weeks | 560 hrs | $8,400 | $28,000 |
| Phase 3 — Scale | 24 weeks | 1,640 hrs | $24,600 | $82,000 |
| **TOTAL** | **48 weeks** | **2,800 hrs** | **$42,000** | **$140,000** |

**Recommended team:** 2 senior devs + 1 junior + 1 QA (Bangladesh-based) = ~$8,000/month
**Break-even at:** 200 clients × avg ৳5,000/mo = ৳10,00,000/mo (~$9,000/mo)

---

## Phase 0 — Foundation (Weeks 1–4)

### 0.1 Infrastructure Setup
| Task | Hours | Owner |
|---|---|---|
| Register bengalbound.io domain + Cloudflare setup | 2 | DevOps |
| Hetzner VPS + IAM + Secret Manager | 4 | DevOps |
| Railway.app PostgreSQL + env setup | 2 | DevOps |
| GitHub Actions CI/CD skeleton | 6 | DevOps |
| Cloud Run + Vercel deploy pipelines | 3 | DevOps |
| **Subtotal** | **17 hrs** | |

### 0.2 Django Backend Scaffold
| Task | Hours | Owner |
|---|---|---|
| Django 4.2 LTS project init + settings (dev/prod split) | 4 | Backend Dev |
| Custom User model + django-allauth integration | 8 | Backend Dev |
| Role-based access control (RBAC) | 6 | Backend Dev |
| Subscription model + tier enforcement | 6 | Backend Dev |
| AI Provider abstraction layer (LiteLLM proxy (LITELLM_BASE_URL) + Ollama + OpenAI-compat) | 10 | Backend Dev |
| diskcache session + rate limiting | 4 | Backend Dev |
| django-apscheduler setup | 3 | Backend Dev |
| Docker + Gunicorn + Nginx on VPS deployment | 6 | DevOps |
| **Subtotal** | **47 hrs** | |

### 0.3 Inspector Module
| Task | Hours | Owner |
|---|---|---|
| ComplianceRule model + 40+ rule preload | 10 | Backend Dev |
| Pre-execution 5-check synchronous pipeline | 16 | Backend Dev |
| SHA-256 append-only audit log | 8 | Backend Dev |
| Fail-closed middleware | 4 | Backend Dev |
| Slack + PagerDuty alert integration | 6 | Backend Dev |
| Inspector health endpoint | 2 | Backend Dev |
| Inspector admin dashboard (internal) | 8 | Backend Dev |
| **Subtotal** | **54 hrs** | |

### 0.4 Veritas KYB Module
| Task | Hours | Owner |
|---|---|---|
| Client application models + API | 8 | Backend Dev |
| OpenCorporates API integration | 8 | Backend Dev |
| OpenSanctions API integration | 6 | Backend Dev |
| Google Vision OCR document processing | 8 | Backend Dev |
| Risk scoring algorithm | 6 | Backend Dev |
| Digital agreement signing + storage | 6 | Backend Dev |
| Admin review queue | 4 | Backend Dev |
| **Subtotal** | **46 hrs** | |

### 0.5 Core Notifications + Auth
| Task | Hours | Owner |
|---|---|---|
| Notification models (admin + user) | 6 | Backend Dev |
| FCM push notification dispatcher | 8 | Backend Dev |
| Gmail SMTP + SendGrid integration | 4 | Backend Dev |
| MFA (TOTP) setup + verification | 8 | Backend Dev |
| Password reset flow | 4 | Backend Dev |
| Device registry + session management | 6 | Backend Dev |
| Brute-force protection + rate limiting | 4 | Backend Dev |
| **Subtotal** | **40 hrs** | |

### 0.6 QA + Documentation
| Task | Hours | Owner |
|---|---|---|
| Unit tests (pytest-django) for Inspector + Veritas | 8 | QA |
| API documentation (OpenAPI/Swagger) | 4 | Backend Dev |
| .env.example + deployment runbook | 3 | DevOps |
| **Subtotal** | **15 hrs** | |

**Phase 0 Total: 219 hrs (~$3,285 BD / $10,950 Intl)**

---

## Phase 1 — MVP: Console + First 2 Agents (Weeks 5–12)

### 1.1 Console Dashboard (Django templates)
| Task | Hours | Owner |
|---|---|---|
| Project setup + auth guards (django-allauth) | 6 | Frontend Dev |
| Design system + Tailwind config + dark theme | 8 | Frontend Dev |
| Layout: sidebar nav + mobile bottom bar | 10 | Frontend Dev |
| Dashboard home (agent status grid, activity feed) | 16 | Frontend Dev |
| Notification centre (real-time SSE + approval actions) | 20 | Frontend Dev |
| Agent Store + Hire flow | 12 | Frontend Dev |
| Agent Config page (per-agent wizard) | 12 | Frontend Dev |
| Billing portal (Stripe + NowPayments) | 12 | Frontend Dev |
| Team management (invite/remove members) | 8 | Frontend Dev |
| FAQ + Support ticket page | 6 | Frontend Dev |
| Tutorial/onboarding flow (first-time users) | 8 | Frontend Dev |
| Analytics dashboard (Recharts + Nivo) | 14 | Frontend Dev |
| Settings (profile, MFA, security, notifications) | 8 | Frontend Dev |
| Mobile responsive review + polish | 10 | Frontend Dev |
| **Subtotal** | **150 hrs** | |

### 1.2 Concierge Agent
| Task | Hours | Owner |
|---|---|---|
| WhatsApp Business webhook + verification | 8 | Backend Dev |
| Embeddable web chat widget (vanilla JS) | 10 | Frontend Dev |
| LiteLLM proxy (LITELLM_BASE_URL) conversation + qualification flow | 12 | Backend Dev |
| Knowledge base CRUD | 6 | Backend Dev |
| Google Calendar booking integration | 8 | Backend Dev |
| Handoff brief PDF generation | 4 | Backend Dev |
| Nurture sequence scheduler | 4 | Backend Dev |
| Inspector integration + user notifications | 4 | Backend Dev |
| Console config page | 6 | Frontend Dev |
| **Subtotal** | **62 hrs** | |

### 1.3 Serea Agent
| Task | Hours | Owner |
|---|---|---|
| Meta Graph API OAuth + page connection | 8 | Backend Dev |
| 30-minute content polling (apscheduler) | 4 | Backend Dev |
| LiteLLM proxy (LITELLM_BASE_URL) content classification pipeline | 10 | Backend Dev |
| Auto-hide/delete with confidence threshold | 6 | Backend Dev |
| Crisis detection + alert system | 6 | Backend Dev |
| Auto-reply from knowledge base | 6 | Backend Dev |
| Inspector integration + user notifications | 4 | Backend Dev |
| Console config page + moderation dashboard | 8 | Frontend Dev |
| **Subtotal** | **52 hrs** | |

### 1.4 Billing + Payments
| Task | Hours | Owner |
|---|---|---|
| NowPayments webhook handler + tier activation | 10 | Backend Dev |
| Stripe subscription portal | 8 | Backend Dev |
| Usage metering per agent | 6 | Backend Dev |
| Tier enforcement + auto-pause | 4 | Backend Dev |
| PDF invoice generation + email | 6 | Backend Dev |
| **Subtotal** | **34 hrs** | |

### 1.5 Testing + Launch
| Task | Hours | Owner |
|---|---|---|
| End-to-end testing (Playwright) | 16 | QA |
| Security penetration test preparation | 8 | Backend Dev |
| Load testing (first 10 clients) | 4 | DevOps |
| Bug fixing + polish | 16 | All |
| Beta client onboarding (5 clients) | 8 | All |
| **Subtotal** | **52 hrs** | |

**Phase 1 Total: 350 hrs (~$5,250 BD / $17,500 Intl)**

---

## Phase 2 — Core Agents Suite (Weeks 13–24)

### 6 Core Agents (2 weeks each × 6)
Each agent follows: Models → Inspector gate → API → Console config → Notifications → Analytics

| Agent | Key Integration | Hours |
|---|---|---|
| Lead Hunter | Apollo.io + HubSpot | 60 hrs |
| Content Architect | WordPress API + Google Drive | 60 hrs |
| Ad Optimizer | Google Ads API + Meta Marketing API | 70 hrs |
| Reporting Bot | GA4 API + Meta Ads + PDF report | 55 hrs |
| Oracle | Google Search Console + rank tracking | 55 hrs |
| Iris | Gmail API + triage + drafts | 55 hrs |
| **Subtotal** | | **355 hrs** |

### Web App MVP (Django templates — mobile deferred)
| Task | Hours |
|---|---|
| Project setup + django-allauth + auth | 20 hrs |
| Notification centre + approval actions | 30 hrs |
| Dashboard home + agent status | 20 hrs |
| Agent activity feed (real-time SSE) | 15 hrs |
| Basic analytics (Chart.js) | 15 hrs |
| Billing screen | 10 hrs |
| Settings + MFA setup | 12 hrs |
| QA + deployment | 20 hrs |
| **Subtotal** | **142 hrs** |

### QA + Performance
| Task | Hours |
|---|---|
| Full regression test suite | 20 hrs |
| API performance profiling | 10 hrs |
| Database index optimization | 8 hrs |
| Security audit | 16 hrs |
| **Subtotal** | **54 hrs** |

**Phase 2 Total: 551 hrs (~$8,265 BD / $27,550 Intl)**

---

## Phase 3 — Scale: All Agents + Desktop (Weeks 25–48)

### Remaining 22+ Agents
| Batch | Agents | Hours/Agent | Total |
|---|---|---|---|
| Batch A | Aria, Kai, Hera, Finn, Crux, Sage | 65 hrs | 390 hrs |
| Batch B | Plex, MediBook, Realt, Merch, Babel, Nova | 60 hrs | 360 hrs |
| Batch C | Rex, Mira, Shield, Pulse, Scout, Luma, Atlas, Cash, Dox, Tempo, Flux, Nexus, Payload, Clarity | 55 hrs | 770 hrs |
| **Subtotal** | | | **1,520 hrs** |

### Desktop Apps (macOS + Windows + Linux)
| Task | Hours |
|---|---|
| macOS app + system tray | 40 hrs |
| Windows app + taskbar | 35 hrs |
| Linux app + AppImage + Snap | 25 hrs |
| App Store submissions (all platforms) | 15 hrs |
| **Subtotal** | **115 hrs** |

**Phase 3 Total: 1,635 hrs (~$24,525 BD / $81,750 Intl)**

---

## Team Structure (Bangladesh-Based)

| Role | Monthly Cost (BDT) | Monthly Cost (USD) |
|---|---|---|
| Senior Full-Stack Dev (Django + React) | ৳80,000 | ~$730 |
| Senior Full-Stack Dev (Django + React) | ৳80,000 | ~$730 |
| Web Developer (Django templates) | ৳70,000 | ~$640 |
| QA Engineer | ৳50,000 | ~$455 |
| **Total Team/Month** | **৳2,80,000** | **~$2,555** |

**Total 12-month burn rate (team only):** ~$30,660
**Add infrastructure ($100/mo):** ~$1,200/year
**Add API costs (LiteLLM, Twilio, etc.):** ~$2,400/year
**Total 12-month operational cost:** ~**$34,260**

---

## Timeline to Live (2026)

| Milestone | Target Date |
|---|---|
| Phase 0 complete (API live, Inspector running) | July 2026 |
| Phase 1 complete (Console + 2 agents + first clients) | September 2026 |
| **Public Beta Launch (Bangladesh)** | **October 2026** |
| Phase 2 complete (8 agents + web app) | December 2026 |
| **Full Public Launch (Global)** | **January 2027** |

---

*BengalBound Ltd WBS v1.0 — NeurolinkIT Confidential*
