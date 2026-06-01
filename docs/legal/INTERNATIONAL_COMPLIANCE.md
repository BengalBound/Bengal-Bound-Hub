# International Compliance Guide
# BengalBound HUB — BengalBound Ltd
**Version:** 1.0 | **Date:** June 2026 | **Owner:** Legal / DPO

---

## Overview

BengalBound operates in a multi-jurisdiction environment. This document covers legal requirements per region, what is already implemented in the codebase, and what remains to be done before entering each market.

---

## 1. European Union — GDPR

**Regulation:** General Data Protection Regulation (GDPR) — Effective May 2018  
**Applies to:** Any platform processing data of EU residents, regardless of company location.

### What We Have
- Data deletion capability (Django admin + model history)
- Encrypted model fields (Fernet via `django-encrypted-model-fields`)
- Audit trail (`django-simple-history` on BusinessInstance + employees)
- IP access controls (`BusinessAccessMiddleware`)
- HTTPS enforced in production (`SECURE_SSL_REDIRECT = True`)

### What We Need
- [ ] **Privacy Policy** page at `/privacy/` (legal document drafted by lawyer)
- [ ] **Terms of Service** page at `/terms/`
- [ ] **Cookie consent banner** (use `django-cookie-consent` or JS banner)
- [ ] **Data Subject Request form** — right to access, right to erasure
- [ ] **DPO appointment** (required if processing large-scale EU data)
- [ ] **Data Processing Agreements (DPAs)** with Supabase, Render, Groq
- [ ] **GDPR-compliant email unsubscribe** in all marketing emails
- [ ] **Explicit consent logs** for account creation + marketing

### Article 13 Disclosure (on signup)
Must tell users: what data is collected, why, how long kept, who it's shared with.

---

## 2. EU AI Act

**Effective:** August 2026 (phased rollout)  
**Risk Classification for BengalBound:** **Limited Risk** (AI systems that interact with humans)

### Requirements for Limited Risk AI
- [ ] **Transparency notice** when users interact with AI agents (disclose it's AI)
- [ ] **Human oversight mechanism** — already implemented (AgentPermissionRequest flow)
- [ ] **Logging** — AgentLog model already captures every action
- [ ] **Opt-out option** — users must be able to reject AI-assisted decisions

### Our HITL (Human-in-the-Loop) Architecture
BengalBound already has a compliant architecture:
- Every agent raises `AgentPermissionRequest` for low-confidence decisions
- Business owner approves/denies before action is taken
- Full audit trail in `AgentLog`
- Agents can be paused/fired via console

---

## 3. United Kingdom — UK GDPR

Post-Brexit, UK has its own version of GDPR (near-identical).

- [ ] UK ICO registration (required if processing UK personal data)
- [ ] UK-specific Privacy Policy addendum
- [ ] UK representative if no UK establishment

UK ICO registration fee: £40–60/year for small organisations.

---

## 4. Bangladesh — Cybersecurity Act + Digital Security Act

**Applies to:** All operations from Bangladesh.

### Requirements
- [ ] Register with Bangladesh Telecommunication Regulatory Commission (BTRC) if handling communications data
- [ ] Local data storage option (self-hosted plan)
- [ ] Encryption of sensitive data at rest — **already implemented** (Fernet fields)
- [ ] No cross-border transfer of national security-related data
- [ ] RJSC company registration (required to collect payments legally)
- [ ] TIN (Tax Identification Number) registration
- [ ] VAT registration if revenue > BDT 3,000,000/year

---

## 5. Singapore — PDPA

**Regulation:** Personal Data Protection Act  
**Applies to:** Any organisation collecting/using/disclosing personal data of Singapore residents.

### Requirements
- [ ] Designate a Data Protection Officer (DPO)
- [ ] Publish a Data Protection Policy
- [ ] Implement Do Not Call registry checks for marketing calls
- [ ] Data breach notification within 3 days
- [ ] Transfer limitation clause for cross-border data

---

## 6. United States — CCPA + State Laws

**Applies to:** Businesses serving California residents with > $25M revenue OR > 50,000 records.

### CCPA Requirements (when applicable)
- [ ] Right to know (data disclosure on request)
- [ ] Right to delete
- [ ] Right to opt-out of data sale
- [ ] "Do Not Sell My Personal Information" link in footer

### CAN-SPAM (Email Marketing)
- [ ] Physical address in all marketing emails
- [ ] Clear unsubscribe link
- [ ] Honor unsubscribe requests within 10 days

---

## 7. UAE — PDPL

**Regulation:** Personal Data Protection Law (Federal Decree-Law No. 45 of 2021)

### Requirements
- [ ] Data Protection Officer designated
- [ ] Data localisation: sensitive data of UAE residents must be stored in UAE (or with adequate safeguards)
- [ ] Explicit consent before collecting sensitive personal data
- [ ] Data breach notification to regulator
- [ ] Consider UAE/GCC cloud hosting for Tier 1 UAE clients

---

## 8. India — DPDP Act (2023)

**Digital Personal Data Protection Act — effective gradually through 2025–2026**

### Requirements
- [ ] Consent manager integration
- [ ] Purpose limitation (data only used for stated purpose)
- [ ] Data fiduciary registration (if significant data processor)
- [ ] Grievance officer appointed for India
- [ ] Data localisation for sensitive categories

---

## 9. Universal Requirements (All Markets)

These apply everywhere regardless of jurisdiction:

| Requirement | Status | Notes |
|---|---|---|
| Privacy Policy page | Needed | Draft with lawyer |
| Terms of Service page | Needed | Draft with lawyer |
| Cookie consent | Needed | Use `django-cookie-consent` |
| SSL/HTTPS | Done | `SECURE_SSL_REDIRECT = True` |
| Data encryption at rest | Done | Fernet fields + DB encryption |
| Audit logging | Done | `django-simple-history` |
| Human-in-the-loop AI | Done | AgentPermissionRequest |
| AI transparency notice | Needed | Show "AI Agent" label in chat UI |
| Data deletion capability | Partial | Admin works, user-facing endpoint needed |
| Breach notification process | Needed | Define SLA + contacts |

---

## 10. Immediate Legal Actions Before Launch

Priority order:

1. **Register company** — Bangladesh (RJSC) + Wyoming LLC for US/global operations
2. **Draft Privacy Policy + Terms of Service** — hire a SaaS lawyer (Clerky, Stripe Atlas Legal)
3. **Register TIN + VAT** (Bangladesh)
4. **Open business bank account** + Stripe account (needs company registration)
5. **Appoint DPO** or designate a team member as data protection contact
6. **Add cookie consent banner** to public site
7. **Add AI transparency disclosures** to agent chat interfaces
8. **Set up GDPR data request form** (can be simple email-based initially)

---

## 11. Resources

| Resource | Use |
|---|---|
| iubenda.com | Auto-generate GDPR-compliant Privacy Policy + Cookie Policy |
| Stripe Atlas | US company formation + bank account |
| Clerky | Legal document templates for SaaS |
| RJSC Bangladesh | Company registration portal |
| ICO UK | ico.org.uk — UK data protection registration |
| PDPC Singapore | pdpc.gov.sg — Singapore PDPA guidance |
