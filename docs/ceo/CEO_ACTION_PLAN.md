# CEO Action Plan — BengalBound HUB
**Date:** June 2026 | **Status:** Post-Deployment Phase

The core backend and database are now successfully deployed on Google Cloud Run and Supabase. The platform is technically live. This document outlines the immediate commercial, operational, and marketing steps required to transition from a deployed backend to a revenue-generating business.

---

## 1. Commercial Infrastructure Setup
Before onboarding users, the billing and communication infrastructure must be finalized.

- [ ] **Stripe Integration:** Create a Stripe account and generate Live `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY`. This is required to process SaaS subscriptions and AI agent hiring fees.
- [ ] **Transactional Email:** Set up Brevo or Mailgun (free tier covers 300 emails/day). Provide the SMTP credentials to the CTO to enable user registration emails and password resets.
- [ ] **Domain Registration & DNS:** Secure `bengalbound.com`. Set up Cloudflare (free tier) to manage DNS routing for the main site and subdomains (`workspace.`, `console.`, `community.`).

## 2. Marketing & Public Site Launch
The backend is live, but the public-facing storefront needs to be published.

- [ ] **Deploy Marketing Site:** Connect the GitHub repository to Cloud Run to automatically build and host the public marketing site (`bengalbound.com`).
- [ ] **Social Media Presence:** Create official LinkedIn, Facebook, and Instagram accounts. These are necessary not just for marketing, but to test the "Serea" AI social media manager agent.
- [ ] **Launch Materials:** Finalize the "See BengalBound in Action" video demo and ensure the "Platform Overview Tutorial" is uploaded to YouTube.

## 3. Beta Onboarding & Sales
Start generating initial feedback and MRR.

- [ ] **Target Top 5 Prospects:** Identify 5 local SMEs in Bangladesh or the UK diaspora to act as closed-beta testers. Focus on onboarding them to the Entry/Standard tiers.
- [ ] **Affiliate Program Setup:** Define the 20–30% recurring commission structure and identify the first 3 agency partners to resell the platform.

## 4. Funding & Grants
Leverage the "built in Bangladesh for the world" narrative.

- [ ] **Apply for SME Grants:** Submit applications for USAID or Gates Foundation SME technology grants, highlighting how BengalBound democratizes AI for developing markets.
- [ ] **Prepare Pitch Deck:** Ensure the AI Video Pitch Presenter agent (Sylvia) is loaded with the latest financial projections ($216K ARR Year 1 target) for angel investor outreach.

## 5. Telephony & Global Operations
- [ ] **Acquire International Phone Numbers:** Purchase local Twilio numbers (e.g., UK +44, US +1) to serve as dedicated entry points for the multi-country AI call center.
- [ ] **Configure Regional Call Queues:** Integrate the new numbers with the `CallQueue` module and set the Voice Receptionist's `language_code` and `tts_voice` appropriately for each region (e.g., French, Spanish, Bengali).
