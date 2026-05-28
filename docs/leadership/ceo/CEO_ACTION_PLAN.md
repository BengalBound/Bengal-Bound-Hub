# CEO Master Action Plan — BengalBound HUB
# Bengal Bound Product Launch: Bangladesh → Global
**Owner:** CEO / Founder
**Starting Point:** Trade License obtained ✅
**Goal:** Go live with Bengal Bound by October 2026

---

> **HOW TO USE THIS:** Work through each week's tasks in order.
> Tick each box when done. Share status in weekly team meetings.
> This document is your operating playbook for the next 12 months.

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

### Week 5: Server Infrastructure Setup (VPS + Ollama)
*   **Hetzner Cloud Setup:** Order Hetzner CX42 VPS (startup tier, 8 vCPUs, 16GB RAM) at Germany location ($19/mo).
*   **Ollama Installation:** SSH to server, run `curl -fsSL https://ollama.ai/install.sh | sh` and pull models (`mistral:7b`, `phi3:mini`).
*   **Firebase Integration:** Create Firebase project `bengalbound` and setup Authentication.

### Week 6: Development Host Setup
*   Setup high-performance Ryzen/i9 local developer workstations (32GB RAM minimum, UPS power backups).
*   Clone the repository and verify local environment builds correctly.

### Week 7: Team Hiring
*   Post job ads on LinkedIn Jobs and tech groups for:
    *   2 Senior Full-Stack Developers (Django + React)
    *   1 Flutter Developer
    *   1 QA Engineer
*   Draft employment agreements incorporating intellectual property transfer clauses.

### Week 8: Payments & U.S. LLC Setup
*   **Wyoming LLC:** Form Wyoming LLC using Stripe Atlas or Doola to open U.S. Stripe and Mercury accounts.
*   **NowPayments:** Set up NowPayments first for seamless cryptocurrency checkpoints.
*   **Local Gateways:** Setup bKash and Nagad Business merchant accounts.

---

## MONTH 3–4 — Product Development & NGO Launch

*   Onboard the development team and initiate Sprint A (Foundation) and B (Domain Models).
*   **RJSC Registration:** Register as a Social Enterprise to establish USAID / Gates Foundation grant eligibility.
*   Onboard first 5 free NGO clients under our social impact tier.

---

## MONTH 5–6 — Beta Launch & AppSumo LTD

*   Transition from closed beta program to public beta.
*   **AppSumo LTD Campaign:** Submit lifetime deal packages to AppSumo.
*   **Upwork/Fiverr:** Set up custom "DFY" (Done For You) implementation and setup gigs.

---

## MONTH 7–12 — Enterprise Scaling & Series A

*   Scale SaaS subscriptions to 50 active commercial clients.
*   Hiring expansion, BASIS venture fundraising, and scale Hetzner VPS nodes.
