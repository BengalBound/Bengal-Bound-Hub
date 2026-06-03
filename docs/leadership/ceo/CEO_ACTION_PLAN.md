# CEO Master Action Plan — BengalBound HUB
# Bengal Bound Product Launch: Bangladesh → Global
**Owner:** CEO / Founder
**Starting Point:** Trade License obtained ✅
**Goal:** Go live with Bengal Bound by October 2026
**Last Updated:** June 2026

---

> **HOW TO USE THIS:** Work through each week's tasks in order.
> Tick each box when done. Share status in weekly team meetings.
> This document is your operating playbook for the next 12 months.

---

## CURRENT TECHNOLOGY STATUS (June 2026)

| Milestone | Status | Notes |
|-----------|--------|-------|
| Trade License | ✅ Done | Obtained |
| Sprint A — 30 Agents Migrated | ✅ Done | All 30 agents live in `agents/` |
| Sprint B — Domain Models | ✅ Done | All migrations applied |
| Google Cloud Run Deployment | ✅ Live | `bengal-bound-hub` · `us-south1` |
| Production PostgreSQL | ✅ Live | Supabase · `aws-1-us-east-1.pooler.supabase.com` |
| Twilio Voice Receptionist | ✅ Done | `+18664030430` wired to Aria agent |
| API Documentation (Swagger) | ✅ Live | `/api/docs/` on Cloud Run |
| CI Test Suite | ✅ Passing | 219 tests · 0 failures |
| drf-spectacular schema warnings | ✅ Fixed | All 32 ViewSets cleaned |
| Wyoming LLC | ⏳ Pending | See Month 2 |
| AppSumo LTD Campaign | ⏳ Pending | See Month 5-6 |
| Bangladesh NGO Clients | ⏳ Pending | See Month 3-4 |

---

## MONTH 1 — Legal Foundation (Weeks 1–4)

### Week 1: Company & Tax Setup
- [ ] **Apply for TIN (Tax Identification Number)**
  - Where: National Board of Revenue (NBR) → [etaxnbr.gov.bd](https://etaxnbr.gov.bd)
  - Bring: Trade License + NID + Passport photo
  - Cost: Free | Time: 1–3 days
- [ ] **Apply for VAT Registration**
  - Where: Local VAT Circle Office or VAT online portal
  - Bring: TIN + Trade License + Bank statement
  - Cost: Free | Time: 7–14 days
- [ ] **Confirm company address** on all documents (must match trade license address)
  - If home/rented office — ensure lease agreement available
- [ ] **Open Bengal Bound company email**
  - Recommended: Google Workspace (info@bengalbound.com, ceo@bengalbound.com)
  - Cost: $6/user/month

### Week 2: Bank Account
- [ ] **Open Business Bank Account** (Current Account)
  - Recommended banks: Dutch-Bangla Bank / City Bank / BRAC Bank
  - Required documents (see DOCUMENTS_CHECKLIST.md)
- [ ] **Apply for Foreign Currency (FC) Account**
  - Same bank, same visit — ask for USD account alongside BDT account
  - This is ESSENTIAL for receiving international client payments
- [ ] **Set up mobile banking** (bKash Business or Nagad Business for local payments)

### Week 3: Digital Presence
- [ ] **Register bengalbound.io domain**
  - Registrar: Cloudflare, Namecheap, or GoDaddy (~$10–15/year)
- [ ] **Register bengalbound.com** (company website)
- [ ] **Set up Google Workspace** for company email
- [ ] **Create company social profiles:**
  - LinkedIn Company Page (Bengal Bound)
  - Facebook Page (Bengal Bound)
  - Twitter/X (@bengalboundio)
  - Instagram (@bengalbound.io)
- [ ] **Set up Google Analytics + Search Console** on bengalbound.io

### Week 4: Industry Registration
- [ ] **Apply for BASIS Membership**
  - Where: [basis.org.bd](https://basis.org.bd)
  - Required: Trade License, TIN, incorporation docs
  - Cost: ৳5,000–15,000/year
  - Benefit: Industry credibility, export support, networking events
- [ ] **Apply for ICT Division Startup Registration**
  - Where: startup.gov.bd
  - Benefit: Possible grant/seed funding from government
- [ ] **Apply for Export Registration Certificate (ERC)**
  - Where: Office of Chief Controller of Imports & Exports (CCI&E)
  - Required: Trade License + TIN + Bank certificate
  - Cost: ৳500–2,000 | ESSENTIAL for receiving foreign payments legally

---

## MONTH 2 — Technology & Team (Weeks 5–8)

### Week 5: Server Infrastructure
> Note: Google Cloud Run is already live for the backend (no VPS needed for the app itself).
> Hetzner VPS is used for self-hosted LiteLLM / Ollama AI routing when scaling beyond Cloud Run.

- [x] **Google Cloud Run:** `bengal-bound-hub` service deployed in `us-south1` ✅
- [x] **PostgreSQL:** Supabase production database connected ✅
- [ ] **Hetzner Cloud Setup (AI routing):** Order Hetzner CX42 VPS ($19/mo) at Germany location
  - SSH in, install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
  - Pull models: `ollama pull mistral:7b && ollama pull phi3:mini`
  - Point `LITELLM_BASE_URL` to this VPS
- [ ] **Firebase Integration:** Create Firebase project `bengalbound` for auth (Voice Receptionist)
- [x] **Twilio Voice Receptionist:** `+18664030430` configured, Aria agent active ✅
  - Still needed: Set Twilio env vars in Cloud Run (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER)

### Week 6: Development Environment
- [ ] **Set up high-performance developer workstations** (32GB RAM minimum, UPS power backups)
- [x] **Repository cloned and verified locally** ✅

### Week 7: Team Hiring
- [ ] **Post job ads** on LinkedIn Jobs and tech groups for:
  - 2 Senior Full-Stack Developers (Django + React)
  - 1 Flutter Developer
  - 1 QA Engineer
- [ ] **Draft employment agreements** incorporating intellectual property transfer clauses

### Week 8: Payments & U.S. LLC Setup
- [ ] **Wyoming LLC:** Form Wyoming LLC using Stripe Atlas or Doola to open U.S. Stripe and Mercury accounts
- [x] **NowPayments:** Already integrated in codebase (sandbox configured) ✅
- [ ] **Activate NowPayments:** Switch from sandbox to production API key
- [ ] **Local Gateways:** Setup bKash and Nagad Business merchant accounts

---

## MONTH 3–4 — Product Development & NGO Launch

### Technology (Already Completed ✅)
- [x] Sprint A — 30 AI Agents migrated and seeded (`python manage.py seed_agents`) ✅
- [x] Sprint B — All domain models, ViewSets, serializers, and migrations applied ✅
- [x] 219 automated tests passing on CI ✅
- [x] Swagger API docs live at `/api/docs/` ✅

### Remaining Steps
- [ ] **RJSC Registration:** Register as a Social Enterprise to establish USAID / Gates Foundation grant eligibility
- [ ] **Onboard first 5 free NGO clients** under our social impact tier
  - Set up their `BusinessInstance` records via Django admin
  - Run `python manage.py seed_modules` on their accounts
  - Provide onboarding walkthrough

---

## MONTH 5–6 — Beta Launch & AppSumo LTD

- [ ] **Transition from closed beta to public beta**
  - Set `ALLOWED_HOSTS` and `SITE_URL` to production domain
  - Enable Stripe billing for subscriptions
  - Activate Twilio env vars in Cloud Run (3 vars — see Week 5 above)
- [ ] **AppSumo LTD Campaign:** Submit lifetime deal packages to AppSumo
  - Prepare deal tiers: entry / standard / premium
  - Prepare demo video and landing page
- [ ] **Upwork/Fiverr:** Set up custom "DFY" (Done For You) implementation and setup gigs
- [ ] **Set up Twilio Webhook URLs in console** for `+18664030430`:
  - Voice webhook (inbound): `https://bengal-bound-hub-u5i67kezxa-vp.a.run.app/agents/voice-receptionist/webhook/inbound/`
  - Status callback: `https://bengal-bound-hub-u5i67kezxa-vp.a.run.app/agents/voice-receptionist/webhook/transfer-complete/`

---

## MONTH 7–12 — Enterprise Scaling & Series A

- [ ] Scale SaaS subscriptions to **50 active commercial clients**
- [ ] Hiring expansion (target: 10 full-time employees)
- [ ] BASIS venture fundraising outreach
- [ ] Scale Hetzner VPS nodes (see VPS_PROFIT_MODEL.md for thresholds)
  - 50 clients → upgrade to AX52 ($56/mo), add `llama3:8b` or `qwen2.5:14b`
  - 300 clients → upgrade to AX102 ($292/mo)
  - 1,000+ clients → Dedicated GPU instances

---

## IMMEDIATE NEXT ACTIONS (CEO Priority Queue)

1. **Twilio Cloud Run env vars** — run this in Google Cloud Console terminal (use values from `.env`):
   ```bash
   gcloud run services update bengal-bound-hub \
     --region us-south1 \
     --project serea-ai-agent-489222 \
     --set-env-vars "TWILIO_ACCOUNT_SID=<from .env>,TWILIO_AUTH_TOKEN=<from .env>,TWILIO_PHONE_NUMBER=<from .env>"
   ```

2. **Twilio Console webhook setup** — Go to [console.twilio.com](https://console.twilio.com), select `+18664030430`, set:
   - Voice webhook: `https://bengal-bound-hub-u5i67kezxa-vp.a.run.app/agents/voice-receptionist/webhook/inbound/`
   - Status callback: `https://bengal-bound-hub-u5i67kezxa-vp.a.run.app/agents/voice-receptionist/webhook/transfer-complete/`

3. **RJSC & legal filings** — see DOCUMENTS_CHECKLIST.md

4. **Hetzner VPS + Ollama** — needed before self-hosted AI routing (currently running on Groq API via LiteLLM)

5. **AppSumo deal preparation** — demo video + landing page

---

## KEY LINKS

| Resource | URL |
|----------|-----|
| Cloud Run Console | https://console.cloud.google.com/run/detail/us-south1/bengal-bound-hub?project=serea-ai-agent-489222 |
| Live API Docs | https://bengal-bound-hub-u5i67kezxa-vp.a.run.app/api/docs/ |
| Supabase Dashboard | https://supabase.com/dashboard |
| Twilio Console | https://console.twilio.com |
| GitHub (primary) | https://github.com/Adre-melech/BengalBound |
| GitHub (hub org) | https://github.com/BengalBound/Bengal-Bound-Hub |
| GitHub (showcase) | https://github.com/shadman1996/BengalBoundHub |
| NowPayments Sandbox | https://sandbox.nowpayments.io |
