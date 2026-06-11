# BengalBound HUB — Complete Platform Flow

This document describes the end-to-end user journey from first visit to running a fully automated AI-powered business.

---

## The Big Picture

```
PUBLIC SITE (/)
  └── Marketing, pricing, blog, trial request

  ↓  Register / Login

BUSINESS HUB (/hub/<slug>/)
  └── 83 industry-specific modules
  └── Role-based team access (BusinessEmployee)

  ↓  Hire AI Agents

CONSOLE ADMIN (/console/)
  └── 33 AI agents — hire, chat, manage
  └── Billing, notifications, 2FA, reports

  ↓  Agents work autonomously

CELERY BACKGROUND TASKS
  └── Scheduled tasks fire independently
  └── Agents write logs, send alerts, request approvals

  ↓  Human-in-the-loop when needed

APPROVAL FLOW
  └── Agent pauses → email sent → owner approves/denies → agent resumes
```

---

## Step 1 — Register & Verify

**URL:** `/accounts/signup/`

1. Enter email + password
2. Receive verification email — click the link
3. Account is active

**Social login** (Google / GitHub / Facebook) skips email verification.

**Login:** `/accounts/login/` — rate-limited to 5 attempts before lockout.

---

## Step 2 — Enable 2FA (Recommended)

**URL:** `/console/security/totp/setup/`

1. Scan QR code with Google Authenticator or Authy
2. Enter 6-digit code to confirm
3. All future logins require password + TOTP code

---

## Step 3 — Create a Business

**URL:** `/hub/create/`

| Field | Purpose |
|-------|---------|
| Business Name | Display name shown in the hub |
| Slug | URL key — `my-agency` → `/hub/my-agency/` |
| Industry | Drives which modules are shown by default |
| Phone / Address | Used by Voice Receptionist and CRM |

**Industry → Auto-Enabled Modules:**

| Industry | Key Modules Auto-Enabled |
|----------|--------------------------|
| `shop` | POS, Inventory, Invoicing, CRM, Loyalty |
| `restaurant` | POS, Table Mgmt, Inventory, Shift Planning |
| `hotel` | PMS, Channel Manager, Rate Manager, Booking |
| `clinic` | Care Manager, Booking, CRM, Invoicing |
| `school` | SIS, LMS, Assessments, Timetable, Parent Portal |
| `agency` | CRM, Leads, Invoicing, Contracts, Task Board |
| `factory` | ERP, MES, PLM, Production, BOM, QC |
| `real_estate_agency` | Property Listings, Deal Flow, CRM, Commission |
| `dealership` | DMS, DVI, CRM, Workshop, Invoicing |
| `logistics` | TMS, WMS, Inventory, Delivery |
| `business` | CRM, Invoicing, HR, Payroll, Accounting |

---

## Step 4 — Set Up Your Hub

### 4a. Invite Team Members
Hub → Settings → Team → **Invite by email**

Each invited person gets a `BusinessEmployee` record. Non-employees are blocked from all module views.

### 4b. Activate Additional Modules
**URL:** `/console/activate-module/`

Browse 83 available modules by category. Toggle any on. Activated modules appear immediately in the hub sidebar.

### 4c. Freemium Modules (Always On)
Task Board · Team Chat · Announcements · Business Mail · Business Calendar · Cloud Drive · CRM · Invoicing · HR · Expense

---

## Step 5 — Use the Hub Modules

**URL pattern:** `/hub/<business-slug>/<module-prefix>/`

Every module view:
1. Checks the user is authenticated
2. Checks the user is a `BusinessEmployee` of this business
3. Checks the module is activated for this business
4. Cloud Runs module UI scoped to this business only (multi-tenant isolation)

See individual module manuals:
- [CRM & Sales](02_CRM_AND_SALES.md)
- [Finance](03_FINANCE.md)
- [HR & People](04_HR_AND_PEOPLE.md)
- [Inventory & Supply Chain](05_INVENTORY_AND_SUPPLY.md)
- [Retail & Commerce](06_RETAIL_AND_COMMERCE.md)
- [Hospitality](07_HOSPITALITY.md)
- [Healthcare](08_HEALTHCARE.md)
- [Education](09_EDUCATION.md)
- [Real Estate](10_REAL_ESTATE.md)
- [Manufacturing](11_MANUFACTURING.md)
- [Logistics](12_LOGISTICS.md)
- [Travel](13_TRAVEL.md)
- [Productivity & Communication](14_PRODUCTIVITY.md)
- [Analytics & Intelligence](15_ANALYTICS.md)
- [Automotive](16_AUTOMOTIVE.md)

---

## Step 6 — Hire AI Agents

**URL:** `/console/agents/`

1. Browse 33 available agents grouped by category
2. Click **+ Hire** on any agent card
3. Confirm at `/console/hire-ai/`
4. Agent appears in **Active on Your Business** with a status indicator

Each agent is a fully autonomous AI employee with:
- Its own data models linked to your business
- A Celery task scheduler running on an independent schedule
- A REST API at `/hub/<slug>/agents/<agent-slug>/api/`
- Long-term memory and audit log

See [AI Agents Manual](17_AI_AGENTS.md) for full detail on all 33 agents.

---

## Step 7 — Work With Your Agents

### Chat Mode
**URL:** `/console/agents/<agent-slug>/`

Type any instruction. The agent:
1. Reads your message
2. Chooses which tools to use (web search, hub data, API calls)
3. Executes the tools
4. Synthesises the result
5. Replies in the chat panel
6. Writes an `AgentLog` entry

### Autonomous Mode
Celery Beat fires scheduled tasks automatically:
- **Every 30 min:** SLA alerts, incident monitoring, crisis detection
- **Every 2–6 hours:** Scoring, sequencing, health checks
- **Daily (08:00):** Morning digests, overnight summaries
- **Weekly (Mon 07:00):** Pipeline reports, market intel, brand audits
- **Monthly (1st):** Payroll reminders, learning digests

No action needed — agents work in the background.

### API Mode
Any external system can drive an agent:
```
POST /hub/<slug>/agents/<agent-slug>/api/run/
Authorization: Session or Bearer token
{
  "messages": [{"role": "user", "content": "Give me a pipeline summary"}]
}
```

---

## Step 8 — Handle Agent Approvals

When an agent is about to take a consequential action (send an email, update a record, make a purchase), it **pauses and asks for permission**:

```
Agent runs task
  → Low confidence / risky action
  → Creates AgentPermissionRequest
  → Agent status → "waiting" (yellow pip)
  → Email sent to business owner

Business owner:
  → Opens /agents/permission/<id>/respond/
  → Clicks Approve or Deny

If Approved:
  → resume_after_approval Celery task fires
  → Agent completes the action
  → AgentLog records decision

If Denied:
  → Action cancelled
  → Agent returns to "idle"
  → AgentLog records decision
```

Pending approvals appear in the Console notification bell and the agent's workspace panel.

---

## Step 9 — Monitor & Report

### Notifications
**URL:** `/console/notifications/`

Every agent action, approval request, and billing event creates a notification. Bell icon shows unread count.

### Agent Logs
Each agent workspace shows a permanent log of every run:
- Action taken
- Outcome (success / failed / approval-required)
- Duration (ms)
- Full AI output

### Reports
**URL:** `/console/reports/`

Automated daily business intelligence reports compiled by the Reporting Bot agent.

---

## Deployment Surfaces

| Surface | URL | Who uses it |
|---------|-----|-------------|
| Public site | `/` | Visitors, prospects |
| Business hub | `/hub/<slug>/` | Employees |
| Console | `console.yourdomain.com/` | Business owners |
| Workspace | `workspace.yourdomain.com/` | Super-admins |
| Community | `community.yourdomain.com/` | All users |
| Agent API | `/hub/<slug>/agents/<slug>/api/` | External integrations |
| Inbound webhooks | `/agents/webhook/<token>/` | External platforms pushing data |

---

## Security Model

| Layer | How it works |
|-------|-------------|
| Authentication | django-allauth — email + social OAuth |
| 2FA | django-otp TOTP — QR code + 6-digit codes |
| Rate limiting | django-axes — lockout after 5 failures |
| Business isolation | `BusinessAccessMiddleware` — every hub request checks `BusinessEmployee` |
| IP locking | Optional per-business — Premium plan |
| Audit trail | django-simple-history — change log on all core models |
| Encrypted secrets | django-encrypted-model-fields — API keys stored with Fernet |
| Webhook verification | HMAC-SHA256 on all inbound webhook requests |
| HSTS + secure cookies | Enforced in production settings |
