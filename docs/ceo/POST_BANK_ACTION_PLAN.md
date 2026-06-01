# CEO Action Plan: Post-Bank Account Creation

*Date: Phase 1 Commercialization*
*Target: Transitioning from Development Sandbox to Revenue Generation*

Creating the corporate bank account is the trigger event that shifts BengalBound from a "development project" into a **revenue-generating entity**. This document outlines the immediate sequence of actions required to operationalize the business.

---

## Phase 1: Financial & Payment Gateway Integration (Days 1-3)
With the bank account active, the immediate priority is enabling the platform to accept real money.

1. **Stripe Activation (Primary Gateway)**
   - Create a live Stripe account using the official company name and bank details.
   - Complete KYC/KYB (Know Your Business) verification on Stripe.
   - **Technical Step:** Replace the sandbox `STRIPE_PUBLIC_KEY` and `STRIPE_SECRET_KEY` in the Render production environment with the LIVE keys.
   - Configure Stripe Webhooks to point to `https://bengalbound.com/console/webhooks/stripe/`.

2. **NowPayments (Crypto/Alternative)**
   - If utilizing crypto for international clients, link NowPayments payouts to the corporate bank or an associated exchange wallet.
   - Update `NOWPAYMENTS_API_KEY` to live mode.

3. **Accounting & Tax Software Setup**
   - Connect the new bank account to an accounting platform (e.g., Xero, QuickBooks, or Wave for a free start).
   - Establish a simple ledger for SaaS subscription revenue vs. Cloud Infrastructure expenses.

---

## Phase 2: Platform "Go-Live" Checks (Days 4-7)
Before the first marketing push, ensure the platform is legally and technically prepared for paying customers.

1. **Legal Protections**
   - Ensure the **Terms of Service** and **Privacy Policy** (linked in the footer) reflect the official corporate entity name and jurisdiction.
   - Add a Refund Policy (critical for Stripe dispute protection).

2. **End-to-End Real Transaction Test**
   - The CEO must execute a **real $1 transaction** using a personal credit card on the live site to purchase a module or hire an AI.
   - Verify that:
     1. The money hits the Stripe dashboard.
     2. The subscription correctly updates in the BengalBound database.
     3. The AI Agent / Module is successfully unlocked in the Console.
   - Refund the test transaction.

3. **Cloud Infrastructure Funding**
   - Attach the corporate debit/credit card to critical infrastructure:
     - **Render** (Backend Hosting)
     - **Supabase** (Database)
     - **Groq / OpenAI** (AI Inference - buy $50-$100 of initial API credits to prevent agent downtime).

---

## Phase 3: The "Soft Launch" & Initial Revenue (Weeks 2-4)
Do not do a massive public launch yet. Focus on acquiring the first 5-10 paying customers to stress-test the system.

1. **The Founders' Network Drop**
   - Reach out to 10-20 business owners in your immediate network.
   - Offer them a "Founders' Deal" (e.g., 50% off the Pro tier for life) in exchange for being beta testers.
   - Goal: Process $100-$500 in real MRR (Monthly Recurring Revenue) to prove the pipeline.

2. **Affiliate Portal Activation**
   - Turn on the Affiliate Portal in the Console.
   - Onboard 2-3 trusted partners/influencers and provide them with their unique referral links.
   - Instruct them to start pitching the AI Job Portal.

3. **Customer Support Readiness**
   - Ensure the "Support Agent" (Kael/Aelin) or the CRM Support Module is actively monitored by a human.
   - The first few users *will* find bugs. The CEO must act as the ultimate concierge support to ensure high retention.

---

## Phase 4: Scaling & Budget Allocation (Month 2+)
Once the first batch of revenue successfully clears into the bank account without disputes:

1. **Reinvestment Rule**
   - For the first 6 months, strictly enforce a rule: **70% of revenue goes back into marketing and infrastructure**, 30% acts as a cash buffer.
   
2. **Paid Acquisition Launch**
   - Begin deploying targeted Facebook/LinkedIn Ads utilizing the "Hire AI Employees" angle.
   - Budget: $10-$20/day initially, optimizing based on which AI roles (e.g., Social Media Moderator vs. Sales Assistant) generate the most clicks.

3. **Establish Weekly Metrics Review**
   - Track MRR (Monthly Recurring Revenue).
   - Track CAC (Customer Acquisition Cost).
   - Track Churn Rate (are people canceling after 1 month?).
