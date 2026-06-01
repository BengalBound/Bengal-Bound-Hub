# Master UI/UX Workspace & Wireframes Index

Welcome, UI/UX Designer Agent. This document is your single source of truth and entrypoint for the entire Bengal Bound UI/UX ecosystem. It maps all **25 screens** that have been structured and designed as wireframe specifications across the marketing website, user portal console, compliance engine, and web platform.

---

## 🧭 Master Wireframe Map

### 🌐 1. Marketing Website Pages (4 Screens)
- **File:** [docs/design/MARKETING_WIREFRAMES.md](file:///d:/Bengal%20bound/dev-backoffice/docs/design/MARKETING_WIREFRAMES.md)
- **Screens:**
  1. *Homepage Landing:* Main landing, value propositions, and dynamic "Start Free" CTAs.
  2. *Agent Showcase Marketplace:* Multi-category department selector grid displaying status dots.
  3. *Pricing Selector:* Interactive tier matrix showing features and Stripe pricing links.
  4. *Auth Gateways:* django-allauth login/signup overlays and multi-tenant onboarding workspace routes.

### 💻 2. Client Portal & User Console (6 Screens)
- **File:** [docs/design/PORTAL_WIREFRAMES.md](file:///d:/Bengal%20bound/dev-backoffice/docs/design/PORTAL_WIREFRAMES.md)
- **Screens:**
  1. *Console Base Layout:* Collapsible sidebar, top search context bar, organization schema switchers.
  2. *Overview Dashboard:* Executive health vitals, active agent cards, and real-time alerts.
  3. *Veritas Onboarding Wizard:* 3-step corporate registration and OCR document dropzone.
  4. *Billing & Invoicing:* Stripe portal actions, active employee billing details.
  5. *Voice Receptionist Panel:* Call log trackers, LiteLLM proxy spam block indicators, transcript drawers.
  6. *Concierge Inbox Dashboard:* Visual email triage logs, calendar scheduling indicators.

### 🛡️ 3. Compliance Command Centre (6 Screens)
- **File:** [docs/design/COMPLIANCE_WIREFRAMES.md](file:///d:/Bengal%20bound/dev-backoffice/docs/design/COMPLIANCE_WIREFRAMES.md)
- **Screens:**
  1. *Command Centre:* Proactive score widgets, live violations feed, and top triggers list.
  2. *Violation Detail Drawer:* Contextual right slide-out panel outlining AI reasoning.
  3. *Rules Manager CRUD:* Compliance parameters tabular editor and rules toggle switchers.
  4. *Risk Matrix:* Color-coded likelihood vs impact live violation mapper.
  5. *Report Exporter:* Periodic compliance executive PDF generation selector.
  6. *Regulatory Radar:* exposure cards mapping GDPR, CCPA, HIPAA, FCA rules status.

### 🤖 4. Phase 2 AI Employees (6 Screens)
- **File:** [docs/design/PHASE2_AGENT_WIREFRAMES.md](file:///d:/Bengal%20bound/dev-backoffice/docs/design/PHASE2_AGENT_WIREFRAMES.md)
- **Screens:**
  1. *Lead Hunter Panel:* B2B outreach sequencer and email template builders.
  2. *Content Architect Strategy:* SEO planners and Outline Brief generation drawers.
  3. *Aria Support Console:* Ticket categories logs, auto-draft responses, escalation toggles.
  4. *Kai DevOps Console:* CPU/RAM memory performance widgets, Docker statuses, live warning log filters.
  5. *Hera HR Board:* Holiday calendars, leave request tables, and onboarding checklists.
  6. *Nova Data Analyst:* NL-to-SQL query translators and data visualization chart builders.

### 📱 5. Web Application (3 Screens)
- **File:** [docs/design/MOBILE_WIREFRAMES.md](file:///d:/Bengal%20bound/dev-backoffice/docs/design/MOBILE_WIREFRAMES.md)
- **Screens:**
  1. *Overview Dashboard:* High-level metrics, active agent cards, and offline connectivity banners.
  2. *Real-time Approvals Feed:* Actionable alert cards with Approve/Reject buttons.
  3. *Settings:* MFA gates and organization configuration switches.

---

## 🎨 Shared Design Tokens & Principles
Before you begin modifying or executing mockups for any screen, review these mandatory guidelines:
- **Design Tokens:** Follow the strict rules inside [docs/design/UX_PRINCIPLES.md](file:///d:/Bengal%20bound/dev-backoffice/docs/design/UX_PRINCIPLES.md) (8px spacing, 12px card border radius, Inter/Outfit fonts).
- **Core Philosophy:** All designs must pass the **60-Second Rule** (business owners must immediately grasp context) and the **Apple Test** (forgiveness undo toggles, zero learning curve onboarding).
- **Glass-Morphism System (June 2026):** All templates now use the premium glass-morphism design. Key rules: dark background with animated orbs, glass panels (`backdrop-filter: blur(24px)`), cyan (`#00F5D4`) and purple (`#7B2FBE`) accent gradient, Bootstrap 5.3.3 + Bootstrap Icons 1.11.3. Never introduce new CSS frameworks — all styling goes in `index.css` or `console.css`. See [UX_PRINCIPLES.md §BengalBound Design System](UX_PRINCIPLES.md) for full token reference.

---

## 🧑‍💻 UI/UX Designer Agent Handover Guide
If you are modifying layout wireframes:
1. Identify the targeted page section (e.g., Marketing, Portal, Compliance, Web).
2. Edit the corresponding wireframe `.md` specification using clean, readable ascii block shapes.
3. Update the semantic nodes inside [.claude/memory.json](file:///d:/Bengal%20bound/dev-backoffice/.claude/memory.json) to reflect any changes to parent-child screen relations.
4. Record your session details in `AGENT_HANDOFF.md` before stopping.
