# Marketing Website — UI/UX Wireframes

This document details the UI/UX wireframe specifications for the **Bengal Bound** public-facing marketing website.

---

## Canva Marketing Asset Suite
All assets generated and saved to Canva (2026-05-25). Edit links require Canva account access.

| Asset | Canva Design ID | Edit Link |
|-------|----------------|-----------|
| Hero Banner (AppSumo launch poster) | `DAHKvNZZsP8` | https://www.canva.com/d/VF3MAmZDd-1qa2b |
| AppSumo LTD Deal Flyer | `DAHKvMHtpTI` | https://www.canva.com/d/I4JXkCv47ICBT_O |
| Feature Highlight Cards (6 modules) | `DAHKvFv7rh8` | https://www.canva.com/d/sQKhDUjNKdufLvK |
| Agent Showcase Grid (30 agents) | `DAHKvHSrN5s` | https://www.canva.com/d/k_Urs2_AgJFH31e |
| Pricing Comparison Table | `DAHKvCvmBxo` | https://www.canva.com/d/TErmS2yTemPHt8- |
| Twitter/X Social Card | `DAHKvAGxIs4` | https://www.canva.com/d/6uWfmfHSb8gtCah |
| Welcome Email Header | `DAHKvGpqsZ0` | https://www.canva.com/d/gsBYl69Q2zfJ_Fj |
| One-Pager Pitch Proposal | `DAHKvLzNs6M` | https://www.canva.com/d/QZN-Pg7dqpMQVIB |
| OG Image / Facebook Cover | `DAHKvLrz-9o` | https://www.canva.com/d/e2785WcquEZGCao |

**Note on Product Screenshot Carousel:** Requires real dashboard screenshots. Take screenshots of `/dashboard`, `/dashboard/agents`, `/dashboard/compliance`, `/dashboard/veritas`, `/dashboard/billing` once live on VPS, then upload to Canva and assemble carousel.

---

---

## Screen 1: Landing / Homepage
The entry point of the platform, optimized for high conversion ("Start Free" CTA) and showcasing our core value proposition (30+ AI employees managed by Inspector).

```
+-----------------------------------------------------------------------------------+
|  [Logo] Bengal Bound   [Agents] [Pricing] [Legal]               [Start Free] [Login] |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|                   HIRE 24/7 AUTONOMOUS AI EMPLOYEES                                |
|             Directly integrate compliant, active AI agents into                   |
|                   your business workflows in under 60 seconds.                    |
|                                                                                   |
|                        [ Start Free (No Card) ]                                   |
|                                                                                   |
|                  +-----------------------------------------+                      |
|                  |  Search: "I need a content scheduler"  |  [Go]                 |
|                  +-----------------------------------------+                      |
|                                                                                   |
|  +------------------------+  +------------------------+  +---------------------+  |
|  |   COMPLIANCE FIRST     |  |   98% COST REDUCTION   |  |   24/7 OPERATIONS   |  |
|  |  Inspector audits all  |  |  Self-hosted local AI  |  |  No sick days. No   |  |
|  |  actions in real time. |  |  with zero usage fees. |  |  delays. Real work. |  |
|  +------------------------+  +------------------------+  +---------------------+  |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

### Layout Elements:
1. **Global Header:**
   - Left-aligned text/logo mapping to `/` (home).
   - Navigation links with hover transitions.
   - Branded CTA button `t("hero.cta_primary")` with dynamic loading states.
2. **Hero Section:**
   - Multi-line bold heading utilizing "Outfit" or "Inter" typography.
   - Text search field that redirects immediately to `/agents` with pre-filled queries.
3. **Value Props Matrix:**
   - Minimal cards, `border-radius: 12px` and dynamic subtle borders (`border: 1px solid rgba(255,255,255,0.1)`).

---

## Screen 2: Agent Showcase / Marketplace (`/agents`)
A catalog where prospective clients can filter and evaluate the 30+ AI agents.

```
+-----------------------------------------------------------------------------------+
| [Filter by Dept: All | Sales | HR | DevOps | Support | Content | Admin ]          |
+-----------------------------------------------------------------------------------+
| Search: [_________________________]                      Sort: [ Popularity ]     |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +--------------------------+  +--------------------------+  +-----------------+  |
|  | Concierge     [Active]   |  | Serea          [Active]   |  | Voice Rep. [Act]|  |
|  | Executive Assistant      |  | Content Architect        |  | Phone AI Agent  |  |
|  |                          |  |                          |  |                 |  |
|  | ৳1,500/mo (Free Tier)    |  | ৳1,500/mo                |  | ৳2,500/mo       |  |
|  |                          |  |                          |  |                 |  |
|  | [View Spec] [Hire Now]   |  | [View Spec] [Hire Now]   |  | [View Spec] [Hi]|  |
|  +--------------------------+  +--------------------------+  +-----------------+  |
|                                                                                   |
|  +--------------------------+  +--------------------------+  +-----------------+  |
|  | Lead Hunter    [Phase 2] |  | Kai            [Phase 2] |  | Hera   [Phase 2]|  |
|  | Sales Prospector         |  | DevOps Engineer          |  | HR Administrator|  |
|  |                          |  |                          |  |                 |  |
|  | ৳3,000/mo                |  | ৳4,000/mo                |  | ৳3,000/mo       |  |
|  |                          |  |                          |  |                 |  |
|  | [Notify Me] [Spec]       |  | [Notify Me] [Spec]       |  | [Notify Me] [Sp]|  |
|  +--------------------------+  +--------------------------+  +-----------------+  |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

### UX Micro-Interactions:
- **Filtering:** Clicking a department chip performs client-side layout filtering using CSS Transitions without reloading the page.
- **Phase Indicators:** Fully responsive status tags (e.g., green dot for `Active`, amber for `Phase 2/Planned`) with tooltip definitions.

---

## Screen 3: Pricing Page (`/pricing`)
Dynamic subscription calculator and Stripe-integrated plan selector.

```
+-----------------------------------------------------------------------------------+
|                                                                                   |
|                             OUR TRANSPARENT PLANS                                 |
|                     Select the scale that fits your company.                      |
|                                                                                   |
|         +-------------------+  +-------------------+  +-------------------+       |
|         | FREE TIER         |  | GROWTH            |  | ENTERPRISE        |       |
|         |                   |  |                   |  |                   |       |
|         | ৳0 / Month        |  | ৳5,000 / Month    |  | Custom Quote      |       |
|         |                   |  |                   |  |                   |       |
|         | - 1 Active Agent  |  | - 5 Active Agents |  | - 30+ AI Agents   |       |
|         | - Basic Inspector |  | - Full Inspector  |  | - Dedicated VPS   |       |
|         | - 1,000 req/day   |  | - Unlimited req   |  | - Custom Rules    |       |
|         |                   |  |                   |  |                   |       |
|         | [ Get Started ]   |  | [ Choose Growth ] |  | [ Contact Sales ] |       |
|         +-------------------+  +-------------------+  +-------------------+       |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

### Stripe Integration Notes:
- Selection automatically redirects to Stripe Checkout Session with pre-loaded pricing identifiers (`Plan.stripe_price_id`).
- Free Tier utilizes instant onboarding without credit card requirements, generating standard client profiles immediately.

---

## Screen 4: Signup / Login Gate (`/login`, `/signup`)
Minimalist django-allauth gateway with multi-tenant workspace routing.

```
+---------------------------------------------------+
|                                                   |
|                Welcome back to                    |
|                 Bengal Bound                      |
|                                                   |
|      +-------------------------------------+      |
|      | Email: [                         ]  |      |
|      +-------------------------------------+      |
|      +-------------------------------------+      |
|      | Password: [                      ]  |      |
|      +-------------------------------------+      |
|                                                   |
|                 [ Login Now ]                     |
|                                                   |
|                     - or -                        |
|                                                   |
|             [ G ] Sign in with Google             |
|                                                   |
|         New here? [Create Workspace →]            |
+---------------------------------------------------+
```

### UI Rules:
- **Validation:** Instant validation of input forms. Red error banner appears under individual inputs on mismatch.
- **Federated Authentication:** Google Sign-in button triggers popup federated session via django-allauth, automatically triggering `syncDjangoUser()` on response callback.
