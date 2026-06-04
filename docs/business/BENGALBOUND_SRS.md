# Software Requirements Specification (SRS)
# Bengal Bound — AI-as-Employee Platform
**Version:** 1.0 | **By:** NeurolinkIT | **Date:** April 2026
**Classification:** Confidential — Investor & Development Reference

---

## 1. Executive Summary

Bengal Bound is an **AI-as-Employee (AIaaE) marketplace** enabling businesses to hire autonomous AI agents that hold actual job roles, complete real business tasks, and report results 24/7 — supervised by Inspector, an always-on compliance watchdog enforcing 40+ global laws.

### Market Opportunity
| Metric | Value |
|---|---|
| Global AI SaaS market (2026) | $108B |
| AI workforce automation segment | $18B (38% YoY) |
| Target: Bangladesh + SE Asia SMEs | $2.1B addressable |
| Target: Global agency market | $45B+ total addressable |

---

## 2. System Architecture

```
Marketing Site (bengalbound.com)  →  Console (console.bengalbound.com)  →  Web (Django templates) — mobile deferred
                                        ↓
                            Django REST API (api.bengalbound.io)     ← Developer / API portal on .io
                                        ↓
                            INSPECTOR (always-on compliance gate)
                                        ↓
                            AI Engine (LiteLLM proxy (LITELLM_BASE_URL) / Ollama / vLLM — swappable)
                                        ↓
                            30+ Agent Apps (modular, plug-in architecture)
                                        ↓
                            PostgreSQL 16 + Cloud Storage
```

---

## 3. Functional Requirements

### FR-AUTH: Authentication & Security
| ID | Requirement | Priority |
|---|---|---|
| FR-AUTH-01 | Email/password + Google OAuth2 login via django-allauth | Critical |
| FR-AUTH-02 | TOTP MFA (Google Authenticator / Authy) | Critical |
| FR-AUTH-03 | Account lockout after 20 failed attempts | Critical |
| FR-AUTH-04 | New device/location alert to user + admin | High |
| FR-AUTH-05 | Biometric auth (future — deferred with mobile) | High |
| FR-AUTH-06 | Device registry with force-logout | High |
| FR-AUTH-07 | Password reset via secure email link (15min expiry) | Critical |
| FR-AUTH-08 | SSO/SAML 2.0 for enterprise clients (Phase 3) | Medium |

### FR-KYB: Client Onboarding (Veritas)
| ID | Requirement | Priority |
|---|---|---|
| FR-KYB-01 | Company registry verification via OpenCorporates (150+ countries) | Critical |
| FR-KYB-02 | Sanctions screening: OFAC, UN, EU, FATF, UK lists | Critical |
| FR-KYB-03 | Document OCR via Google Vision API | High |
| FR-KYB-04 | Auto-approve Green / queue Amber / reject Red risk | Critical |
| FR-KYB-05 | Digital signature: TOS, DPA, AUP, AI Ethics agreements | Critical |

### FR-INSP: Inspector Compliance Gate
| ID | Requirement | Priority |
|---|---|---|
| FR-INSP-01 | Synchronous pre-execution gate on ALL AI agent outputs | Critical |
| FR-INSP-02 | 5-check pipeline: Legal · Ethics · Cybersecurity · Privacy · Harm | Critical |
| FR-INSP-03 | Fail-closed: agents return 403 if Inspector unavailable | Critical |
| FR-INSP-04 | Append-only audit log with SHA-256 chain, 7-year retention | Critical |
| FR-INSP-05 | Critical violations → Slack + PagerDuty within 60 seconds | Critical |
| FR-INSP-06 | 40+ global laws enforced (GDPR, HIPAA, PDPA, EU AI Act, etc.) | Critical |

### FR-AGENT: AI Agent Framework
| ID | Requirement | Priority |
|---|---|---|
| FR-AGENT-01 | Each agent is self-contained Django app (plug-in architecture) | Critical |
| FR-AGENT-02 | AI provider swappable via env variable (no code changes) | Critical |
| FR-AGENT-03 | Human approval gates on high-stakes actions | Critical |
| FR-AGENT-04 | Usage tracking vs tier limits; auto-pause on limit reached | High |

### FR-NOTIF: Notifications
| ID | Requirement | Priority |
|---|---|---|
| FR-NOTIF-01 | Channels: in-app, email, push (FCM), WhatsApp | High |
| FR-NOTIF-02 | Security events → dev team via Slack + PagerDuty within 60s | Critical |
| FR-NOTIF-03 | Approval notifications include inline Approve/Reject actions | Critical |
| FR-NOTIF-04 | Desktop apps: system tray notifications with quick actions | Medium |

### FR-SUPPORT: Support & Self-Service
| ID | Requirement | Priority |
|---|---|---|
| FR-SUPPORT-01 | Searchable FAQ page | High |
| FR-SUPPORT-02 | Password reset via secure email link | Critical |
| FR-SUPPORT-03 | In-app support ticket submission | High |
| FR-SUPPORT-04 | Step-by-step tutorial for each agent | High |
| FR-SUPPORT-05 | Onboarding email sequence (Day 1, 3, 7, 30) | High |

---

## 4. Non-Functional Requirements

### Security
| Requirement | Target |
|---|---|
| TLS 1.3 in transit | 100% |
| AES-256 at rest | 100% |
| OWASP LLM Top 10 — all mitigated | 100% |
| OWASP Top 10 Web — all mitigated | 100% |
| CVE scanning on every build | Every build |
| Cloudflare WAF active | Always |
| Zero secrets in code/logs | Zero tolerance |
| Penetration test before public launch | Required |

### Performance
| Requirement | Target |
|---|---|
| API p95 response time | < 800ms |
| Marketing site Lighthouse score | > 90 |
| Inspector gate latency | < 500ms |
| Push notification delivery | < 10 seconds |

### Scalability
| Clients | Architecture | No Rewrite Needed |
|---|---|---|
| 0–10 | Gunicorn + Nginx on VPS + Railway DB | ✅ |
| 10–200 | Gunicorn + Nginx on VPS + Supabase/Neon | ✅ Config only |
| 200–1K | Gunicorn + Nginx on VPS + Cloud SQL | ✅ Config only |
| 1K–10K | Multi-region + read replicas | ✅ Infra only |

### Compliance Framework
| Law | Region | Status |
|---|---|---|
| GDPR | EU | ✅ Inspector enforced |
| HIPAA | USA | ✅ MediBook module |
| PDPA | Bangladesh | ✅ Inspector enforced |
| DPDPA | India | ✅ 72hr breach notification |
| PCI DSS v4 | Global | ✅ No raw card data |
| EU AI Act | EU | ✅ Human oversight gates |
| ISO/IEC 42001 | Global | ✅ Inspector + NIST AI RMF |

---

## 5. Key Use Cases

**UC-01:** Client hires Concierge → passes payment → agent activates → handles WhatsApp leads autonomously within minutes.

**UC-02:** Agent tries illegal action → Inspector blocks it → audit logged → client + admin notified in real-time.

**UC-03:** Hacking attempt detected → Rex + Inspector alert dev team via Slack/PagerDuty within 60 seconds → endpoint auto-blocked via Cloudflare API.

**UC-04:** Client loses phone → logs into console → revokes all sessions → re-enables MFA with backup codes.

---

## 6. System Constraints
- Infrastructure budget Phase 0–1: **< $100/month**
- AI provider must be **swappable with 1 env variable**
- No always-on servers except Inspector (Gunicorn + Nginx on VPS min-instances=1)
- No Redis or message queue until 200+ clients (use diskcache + apscheduler)

---

*BengalBound Ltd SRS v1.0 — NeurolinkIT Confidential — Investor Due Diligence Reference*
