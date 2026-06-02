# BengalBound HUB — Complete User Manual & UAT Guide

**Version:** Sprint P3C — 30 AI Agents Live  
**Dev URL:** `http://localhost:1234`  
**Stack:** Django 4.2 · LangChain 1.2 · LangGraph · Celery · Redis · LiteLLM

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Getting Started — Registration & Login](#2-getting-started)
3. [Business Setup & Onboarding](#3-business-setup)
4. [Hub Modules — Complete Reference](#4-hub-modules)
5. [AI Agent Workforce — All 30 Agents](#5-ai-agent-workforce)
6. [Console Admin — Command Centre](#6-console-admin)
7. [User Acceptance Testing (UAT)](#7-uat-test-cases)
8. [Quick Reference & Commands](#8-quick-reference)

---

## 1. System Overview

BengalBound HUB is a **multi-tenant SaaS business operating system**. Each user registers, creates a business, and gets a personalised hub at `/hub/<business-slug>/` with 60+ pluggable modules and a workforce of 30 AI employees.

### Architecture at a Glance

```
PUBLIC SITE (/)
   └─ Marketing, pricing, blog, docs, trial request

BUSINESS HUB (/hub/<slug>/)
   └─ 60+ industry-specific modules
   └─ Role-based team access (BusinessEmployee)

CONSOLE ADMIN (/console/)
   └─ 30 AI agents — hire, chat, manage
   └─ Billing, notifications, 2FA, reports

AI PIPELINE
   LangChain + LangGraph → LiteLLM proxy → Groq / OpenAI
   ↳ Universal tools: web search, scraping, API calls
   ↳ Hub tools: live CRM / HR / Invoice data per business
```

### URL Surface Map

| Surface | URL | Purpose |
|---------|-----|---------|
| Public Site | `/` | Marketing, pricing, login |
| Business Hub | `/hub/<slug>/` | 60+ business modules |
| Console Admin | `/console/` | AI agents, billing, settings |
| Workspace | `/workspace/` | Super-admin workspace |
| Community | `/community/` | Community forum |
| Agent API | `/hub/<slug>/agents/<slug>/api/` | REST API per agent |
| Webhooks | `/agents/webhook/<token>/` | External data ingest |

---

## 2. Getting Started

### 2.1 Registration

**URL:** `/accounts/signup/`

Required fields:
- Email address
- Password + confirmation

After signup → **verification email sent** → must click the link (mandatory). Social OAuth: Google, GitHub, Facebook via `/accounts/`.

### 2.2 Login

**URL:** `/accounts/login/`

- Email + password
- Failed attempts rate-limited by `django-axes` (lockout after 5 failures)

### 2.3 Two-Factor Authentication (TOTP)

**URL:** `/console/security/totp/setup/`

1. Scan the QR code with Google Authenticator or Authy
2. Enter the 6-digit code to activate
3. Every future login requires the 6-digit TOTP after password

### 2.4 Password Reset

Via `/accounts/password/reset/` — standard allauth email flow.

---

## 3. Business Setup

### 3.1 Create a Business

**URL:** `/hub/create/`

| Field | Description |
|-------|-------------|
| Business Name | Display name |
| Slug | URL key — `my-shop` → `/hub/my-shop/` |
| Industry | Drives which modules are prioritised |
| Installation Type | Cloud / IP-Locked / Self-Hosted |

### 3.2 Industry Types & Auto-Enabled Modules

| Industry | Priority Modules |
|----------|-----------------|
| `shop` | POS, Inventory, Invoicing, CRM, Loyalty, Omnichannel |
| `wholesale` | Inventory, Order Mgmt, B2B Portal, WMS, ERP, CRM |
| `retail_chain` | POS, Inventory, Store Ops, Omnichannel, Planogram |
| `restaurant` | POS, Table Mgmt, Inventory, Shift Planning, Loyalty |
| `hotel` | PMS, Channel Manager, Rate Manager, Booking, Table Mgmt |
| `resort` | PMS, Channel Manager, Group Bookings, Loyalty, Data Studio |
| `hostel` | PMS, Booking, Channel Manager, Invoicing, CRM |
| `travel_agency` | Travel CRM, Group Bookings, Travel Desk, Invoicing |
| `tour_operator` | Travel CRM, Group Bookings, Invoicing, Channel Manager |
| `clinic` | Care Manager, Booking, CRM, Invoicing, HR |
| `salon` | Care Manager, Booking, CRM, POS, Loyalty, Payroll |
| `spa` | Care Manager, Booking, CRM, POS, Loyalty, Shift Planning |
| `school` | SIS, LMS, Assessments, Timetable, Parent Portal |
| `university` | SIS, LMS, Assessments, HR, Payroll, Contracts |
| `factory` | ERP, MES, PLM, Production, BOM, Quality Control |
| `warehouse` | Inventory, Delivery, Order Mgmt, Maintenance |
| `agency` | CRM, Leads, Invoicing, Contracts, Task Board, HR |
| `garage` | Workshop, DVI, Invoicing, CRM, Booking |
| `dealership` | DMS, DVI, CRM, Leads, Invoicing, Workshop |
| `logistics` | TMS, WMS, Inventory, Delivery, CRM, HR |
| `consulting` | Process Mapper, Data Studio, CRM, Invoicing, Contracts |
| `legal` | Contracts, Documents, CRM, Invoicing, Task Board |
| `business` | CRM, Invoicing, HR, Payroll, Accounting, Task Board |
| `real_estate_agency` | Property Listings, Deal Flow, CRM, Leads, Commission |
| `other` | CRM, Invoicing, HR, Task Board, Documents |

### 3.3 Freemium Modules (Always Available)

Task Board, Team Chat, Announcements, Business Mail, Business Calendar, Cloud Drive, CRM, Invoicing, HR, Expense.

### 3.4 Invite Team Members

Hub → Settings → Team → Invite by email. New employees get a `BusinessEmployee` record. All module views enforce this — non-employees are blocked.

### 3.5 Activate Modules

**URL:** `/console/activate-module/`

Modules are activated per business. Only activated modules appear in the hub sidebar.

### 3.6 Deployment Options

| Type | Description |
|------|-------------|
| Cloud Hosted | `bengalbound.io/<your-slug>` — available on all plans |
| IP-Locked | Access restricted to your office IP — Premium plan |
| Self-Hosted | Deploy on your own servers — Advance plan |

---

## 4. Hub Modules — Complete Reference

All modules live at `/hub/<business-slug>/<prefix>/`.

---

### 4.1 Sales & CRM

#### CRM (`/crm/`)
Contact management, deal pipelines, activity logging. Full pipeline from lead → prospect → customer.
- Contacts with tags, custom fields, interaction history
- Deal stages with value tracking
- Activity timeline per contact

#### Leads (`/leads/`)
Lead capture, assignment, and qualification workflow.
- Web form integrations
- Lead scoring
- Assignment rules by team member

#### B2B Portal (`/b2b/` — suite prefix)
Self-service portal for business customers to view quotes, place orders, and check order status.

#### Omnichannel (`/omnichannel/` — suite prefix)
Unified inbox — combines messages from email, WhatsApp, social media into one queue.

---

### 4.2 Finance

#### Invoicing (`/invoicing/`)
Create, send, and track invoices. Supports multiple currencies, tax lines, partial payments.

#### Accounting (`/accounting/`)
Chart of accounts, journal entries, bank reconciliation, profit & loss, balance sheet.

#### Payroll (`/payroll/`)
Payroll runs, salary structures, payslip generation, statutory deductions.

#### Expense (`/expense/`)
Employee expense submission, approval workflow, reimbursement tracking.

#### Budgeting (`/budgeting/`)
Budget planning by department. Budget vs actual comparison. Variance alerts.

#### Financials (`/financials/`)
Consolidated financial reporting across departments.

#### Commission (`/commission/` — suite prefix)
Sales commission tracking and payout calculation for real estate / sales teams.

---

### 4.3 HR & People

#### HR (`/hr/`)
Employee records, departments, positions, onboarding checklists, offboarding.

#### Recruitment (`/recruitment/`)
Job postings, applicant tracking, interview pipeline, offer letters.

#### Attendance (`/attendance/`)
Clock-in/out, timesheets, absence tracking, overtime calculation.

#### Shift Planning (`/shifts/`)
Shift scheduling, rota creation, swap requests, coverage alerts.

#### Training (`/training/`)
Internal training programmes, completion tracking, certificates.

#### LMS (`/lms/` — suite prefix)
Full Learning Management System — courses, lessons, quizzes, progress tracking.

#### Assessments (`/assessments/` — suite prefix)
Online assessments with scoring and results reporting.

---

### 4.4 Operations & Projects

#### Task Board (`/board/`)
Kanban-style project management. Cards, columns, due dates, assignees, attachments.

#### Projects (`/projects/`)
Full project management — Gantt, milestones, resources, dependencies.

#### Team Chat (`/chat/`)
Real-time team messaging. Channels, direct messages, file sharing.

#### Announcements (`/announcements/`)
Broadcast messages to the entire team or specific departments.

#### Process Mapper (`/process-mapper/` — suite prefix)
Business process documentation and workflow diagramming.

---

### 4.5 Inventory & Supply Chain

#### Inventory (`/inventory/`)
Stock management, SKUs, warehouses, reorder points, stock movements.

#### Order Management (`/orders/`)
Purchase orders, sales orders, fulfilment tracking.

#### Delivery (`/delivery/`)
Delivery scheduling, driver assignment, tracking, proof of delivery.

#### BOM (`/bom/`)
Bill of Materials — product recipes, component lists, quantity tracking.

#### Production (`/production/`)
Production orders, work orders, capacity planning.

#### Quality Control (`/quality/`)
Inspection checklists, non-conformance reports, quality metrics.

#### Maintenance (`/maintenance/`)
Preventive maintenance schedules, work order management, asset downtime tracking.

---

### 4.6 Retail & Commerce

#### Point of Sale (`/pos/`)
Full POS system — products, variants, discounts, multiple payment methods, receipts.

#### eCommerce (`/ecommerce/`)
Online store management — products, collections, orders, shipping.

#### Loyalty (`/loyalty/`)
Points-based loyalty programme, tiers, redemption rules.

#### Planogram (`/planogram/` — suite prefix)
Store shelf layout planning and compliance tracking.

#### Store Ops (`/store-ops/` — suite prefix)
Multi-store operations management, compliance checklists.

#### Product Catalog (`/product-catalog/` — suite prefix)
Centralised product catalogue with variants, pricing, and images.

---

### 4.7 Hospitality

#### PMS — Property Management (`/pms/`)
Reservations, room management, front desk, housekeeping, guest profiles.

#### Channel Manager (`/channels/`)
Connect to Booking.com, Expedia, Airbnb. Sync availability and rates.

#### Rate Manager (`/rates/`)
Dynamic pricing, rate plans, seasonal rates, yield management.

#### Booking (`/booking/`)
Online appointment / room booking widget and management.

#### Table Management (`/tables/`)
Restaurant floor plan, table assignment, reservations, wait list.

#### Group Bookings (`/groups/`)
Multi-room group reservations, event coordination, group billing.

#### Hospitality Ops (`/hosp-ops/`)
Housekeeping task management, room status, maintenance requests.

---

### 4.8 Healthcare & Personal Care

#### Care Manager (`/care/`)
Patient / client records, care plans, appointment scheduling, notes.

#### Medical Booking (`/booking/`)
Appointment calendar integration for clinics and practitioners.

---

### 4.9 Education

#### SIS — Student Information (`/sis/` — suite prefix)
Student enrolment, academic records, parent contact, fee management.

#### LMS (`/lms/` — suite prefix)
Course delivery, lesson management, student progress, certificates.

#### Assessments (`/assessments/` — suite prefix)
Exam and quiz management, auto-grading, results analytics.

#### Timetable (`/timetable/` — suite prefix)
Class scheduling, room allocation, teacher assignments.

#### Parent Portal (`/parent-portal/` — suite prefix)
Parent-facing portal for attendance, grades, fee payments, announcements.

---

### 4.10 Real Estate

#### Property Listings (`/properties/` — suite prefix)
Property database, listing management, photo galleries, status tracking.

#### Deal Flow (`/deals/` — suite prefix)
Deal pipeline from enquiry → offer → exchange → completion.

#### RE Marketing (`/re-marketing/` — suite prefix)
Email campaigns, property alerts, drip sequences for leads.

#### RE Client Portal (`/re-portal/` — suite prefix)
Client portal for viewing listings, signing documents, and tracking progress.

---

### 4.11 Automotive

#### Workshop (`/workshop/` — suite prefix)
Job cards, technician assignment, parts used, labour tracking.

#### DVI — Digital Vehicle Inspection (`/dvi/` — suite prefix)
Digital inspection forms with photos, customer approval, condition reports.

#### DMS — Dealer Management (`/dms/` — suite prefix)
Full dealership management — inventory, finance, sales pipeline.

---

### 4.12 Manufacturing (Suite Modules)

| Module | URL Prefix | Purpose |
|--------|-----------|---------|
| ERP | `/erp/` | Enterprise resource planning |
| MES | `/mes/` | Manufacturing execution system |
| PLM | `/plm/` | Product lifecycle management |
| CAD/CAM | `/cadcam/` | Design and manufacturing data |
| Asset Management | `/assets/` | Asset register, depreciation, maintenance |

---

### 4.13 Logistics & Freight (Suite Modules)

| Module | URL Prefix | Purpose |
|--------|-----------|---------|
| TMS | `/tms/` | Transport management |
| WMS | `/wms/` | Warehouse management |

---

### 4.14 Travel

#### Travel CRM (`/travel-crm/`)
Travel client profiles, booking history, preferences, communication log.

#### Travel Desk (`/travel-desk/`)
Corporate travel request management, approvals, expense integration.

---

### 4.15 Productivity & Communication

#### Business Mail (`/mail/`)
Business email on your domain — send, receive, folders, templates.

#### Video Meet (`/meet/`)
HD video conferencing — meetings, recordings, screen sharing.

#### Business Calendar (`/calendar/`)
Shared team calendar, event scheduling, meeting rooms.

#### Cloud Drive (`/drive/`)
File storage, folder management, sharing, version history.

#### Docs (`/docs/`)
Rich text document editor — collaborative, formatted, exportable.

#### Sheets (`/sheets/`)
Spreadsheet tool with formulas, charts, and data connections.

#### Slides (`/slides/`)
Presentation builder with templates and real-time collaboration.

#### Forms Builder (`/forms/`)
Create forms, surveys, and data collection tools. Public embed links.

---

### 4.16 Analytics & Intelligence

#### Reports (`/reports/`)
Pre-built business intelligence reports. Export to CSV/PDF.

#### Analytics (AI) (`/analytics/`)
AI-powered analytics — trend detection, anomaly alerts, forecasting.

#### AI Assistant (`/assistant/`)
Conversational AI assistant embedded in the hub for quick queries.

#### Data Studio (`/data/` or `/data-studio/`)
Custom dashboards, drag-and-drop visualisations, data connectors.

#### Dashboard Pro (`/dashboard-pro/`)
Customisable executive dashboard with KPI widgets.

---

### 4.17 Garden & Outdoors

#### Garden Ops (`/garden/`)
Landscaping / nursery / florist job management — scheduling, plant tracking, client quotes.

---

### 4.18 Data & Field Operations

#### Data Collection (`/data/`)
Mobile-friendly data collection forms for field teams.

---

## 5. AI Agent Workforce — All 30 Agents

### 5.1 How Agents Work

Every agent is powered by:
```
User message → LangChain agent + tools → LiteLLM proxy → AI model
                     ↓                         ↑
             Hub tools (CRM/HR/Invoice)    Groq dev fallback
```

Agents have three modes:
1. **Interactive Chat** — manual messages in the workspace
2. **Scheduled Tasks** — Celery background tasks (daily/weekly)
3. **API** — REST calls from external systems

### 5.2 Agent Directory — Full Detail

#### ARIA — Customer Support
- **Slug:** `aria` | **Category:** Support
- Handles inbound support queries, ticket triage, and escalation
- Tools: web search, knowledge base lookup, CRM contact lookup
- Scheduled: daily ticket volume summary

#### ATLAS — Executive Assistant
- **Slug:** `atlas` | **Category:** Operations
- Drafts emails, manages schedules, prioritises tasks, writes briefings
- Tools: web search, calendar data, task board data
- Scheduled: morning priority digest

#### BABEL — Translation Specialist
- **Slug:** `babel` | **Category:** Communication
- Translates documents, emails, and content to/from any language
- Tools: web search for terminology, language detection
- Scheduled: on-demand only

#### CASH — Payroll Processor
- **Slug:** `cash` | **Category:** Finance
- Processes payroll calculations, flags anomalies, generates payslip summaries
- Tools: HR data, payroll module data, tax rate lookup
- Scheduled: weekly payroll audit

#### CLARITY — Feedback Analyst
- **Slug:** `clarity` | **Category:** Analytics
- Analyses customer feedback, identifies sentiment trends, generates insight reports
- Tools: CRM data, web scraping (reviews), analytics data
- Scheduled: weekly feedback digest

#### CONCIERGE — Client Concierge
- **Slug:** `concierge` | **Category:** Operations
- High-touch client journey management, VIP client communications, experience personalisation
- Tools: CRM data, calendar, email drafting
- Scheduled: VIP check-in alerts

#### CONTENT-ARCHITECT — Content Strategist
- **Slug:** `content-architect` | **Category:** Marketing
- Content planning, editorial calendar creation, topic research
- Tools: web search, competitor analysis, trend research
- Scheduled: weekly content plan generation

#### CRUX — CRM Manager
- **Slug:** `crux` | **Category:** Sales
- Pipeline health audits, contact scoring, deal movement recommendations
- Tools: live CRM data (contacts, deals, pipeline stages)
- Scheduled: daily pipeline audit + contact scoring + dormant contact alerts

#### DOX — Technical Writer
- **Slug:** `dox` | **Category:** Documents
- Writes SOPs, manuals, API documentation, internal guides
- Tools: web search, document module access
- Scheduled: on-demand only

#### FLUX — Supply Chain Manager
- **Slug:** `flux` | **Category:** Operations
- Supply chain health monitoring, supplier risk alerts, inventory level analysis
- Tools: inventory data, order data, web search (supplier news)
- Scheduled: daily supply chain health check

#### HERA — HR Agent
- **Slug:** `hera` | **Category:** HR
- Employee lifecycle management, onboarding checklists, policy compliance, leave tracking
- Tools: live HR data (employees, leave, attendance)
- Scheduled: weekly HR digest

#### KAI — DevOps Engineer
- **Slug:** `kai` | **Category:** Technology
- Infrastructure monitoring, incident runbooks, alert triage, deployment summaries
- Tools: web search, API calls to monitoring endpoints
- Scheduled: daily infra health check

#### LEAD-HUNTER — B2B Prospector
- **Slug:** `lead-hunter` | **Category:** Sales
- Finds and qualifies B2B leads, researches prospect companies, drafts outreach
- Tools: web search, web scraping, CRM data (to avoid duplicates)
- Scheduled: daily prospect research

#### LUMA — Brand & PR
- **Slug:** `luma` | **Category:** Marketing
- Brand consistency checks, press release drafting, PR strategy
- Tools: web search, brand guidelines lookup
- Scheduled: weekly brand audit

#### MEDIBOOK — Medical Scheduler
- **Slug:** `medibook` | **Category:** Healthcare
- Appointment scheduling, patient reminders, waitlist management for clinics
- Tools: booking data, patient data
- Scheduled: daily appointment reminders

#### MERCH — eCommerce Manager
- **Slug:** `merch` | **Category:** Commerce
- Product listings, pricing optimisation, promotion planning, inventory alerts
- Tools: inventory data, order data, web search (competitor pricing)
- Scheduled: daily stock level alert

#### MIRA — Customer Success
- **Slug:** `mira` | **Category:** Support
- Customer retention, new customer onboarding, health score monitoring
- Tools: CRM data, invoice data
- Scheduled: weekly churn risk report

#### NEXUS — L&D Coordinator
- **Slug:** `nexus` | **Category:** HR
- Training plans, skills gap analysis, course recommendations
- Tools: HR data, web search (training resources)
- Scheduled: monthly learning digest

#### NOVA — Data Scientist
- **Slug:** `nova` | **Category:** Analytics
- Data analysis, pattern recognition, statistical summaries, forecasting
- Tools: CRM data, HR data, invoice data
- Scheduled: weekly data analysis run

#### ORACLE — SEO Specialist
- **Slug:** `oracle` | **Category:** Marketing
- SEO audits, keyword research, ranking analysis, content gap identification
- Tools: web search, web scraping, competitor analysis
- Scheduled: weekly SEO report

#### PAYLOAD — Procurement Manager
- **Slug:** `payload` | **Category:** Operations
- Purchase order management, supplier evaluation, price benchmarking
- Tools: inventory data, order data, web search
- Scheduled: daily procurement review

#### PULSE — Market Research
- **Slug:** `pulse` | **Category:** Analytics
- Competitor monitoring, market trend analysis, industry news digest
- Tools: web search, web scraping
- Scheduled: daily market pulse report

#### REALT — Real Estate Assistant
- **Slug:** `realt` | **Category:** Real Estate
- Property listings management, client matching, market valuation research
- Tools: property data, CRM data, web search
- Scheduled: weekly listing performance review

#### REPORTING-BOT — Automated Reporting
- **Slug:** `reporting-bot` | **Category:** Analytics
- Generates scheduled business reports — sales, HR, financials, operations
- Tools: CRM data, HR data, invoice data
- Scheduled: daily comprehensive business report

#### SAGE — Legal Reviewer
- **Slug:** `sage` | **Category:** Legal
- Contract review, compliance checks, legal research, risk flagging
- Tools: web search, document module access
- Scheduled: on-demand only

#### SCOUT — Competitor Intelligence
- **Slug:** `scout` | **Category:** Analytics
- Deep competitor research — pricing, product, messaging, weaknesses
- Tools: web search, web scraping
- Scheduled: weekly competitor intel report

#### SEREA-CONTENT — Content Creator
- **Slug:** `serea-content` | **Category:** Marketing
- AI-generated content campaigns — blog posts, social copy, email sequences
- Tools: web search, content research
- Scheduled: weekly content generation

#### SHIELD — IT Helpdesk
- **Slug:** `shield` | **Category:** Technology
- IT support triage, password reset guidance, troubleshooting runbooks
- Tools: web search, knowledge base
- Scheduled: daily IT ticket digest

#### TEMPO — Events Manager
- **Slug:** `tempo` | **Category:** Operations
- Event planning, vendor coordination, timeline management, budget tracking
- Tools: calendar data, CRM data, web search
- Scheduled: event countdown alerts

#### VOICE-RECEPTIONIST — Phone Receptionist
- **Slug:** `voice-receptionist` | **Category:** Communication
- Inbound call scripts, routing logic, message taking, appointment booking
- Tools: booking data, CRM data
- Scheduled: on-demand only

---

### 5.3 Hiring an Agent

1. Go to `/console/agents/` — see Active agents (hired) + Available agents grouped by category
2. Click **"+ Hire"** on any available agent card
3. Confirm at `/console/hire-ai/`
4. Agent appears in **Active on Your Business** panel with status pip

### 5.4 Agent Workspace

**URL:** `/console/agents/<agent-slug>/`

| Panel | Content |
|-------|---------|
| Chat | Type a message, get AI response using live tools |
| Activity Log | All runs — action, outcome, duration, full AI output |
| Pending Approvals | Approval requests the agent is waiting on |

### 5.5 Agent Status Indicators

| Colour | Status | Meaning |
|--------|--------|---------|
| Green pip | `working` | Currently running a task |
| Yellow pip | `waiting` | Paused — needs approval to continue |
| Grey pip | `idle` | Ready, not currently running |
| — | `offline` | Deactivated |

### 5.6 Permission Requests (Human-in-the-Loop)

When an agent needs to take a consequential action, it **pauses and asks for permission**:

1. Agent stops, creates an `AgentPermissionRequest`
2. Status changes to `waiting` (yellow pip)
3. Email sent to business owner with Approve / Deny link
4. Owner approves in workspace or via email link `/agents/permission/<id>/respond/`
5. Denied → action cancelled, agent returns to `idle`
6. Approved → Celery task resumes the action

### 5.7 Agent REST API

All agents share a standard API at `/hub/<biz-slug>/agents/<agent-slug>/api/`:

```
GET  status/               → {status, tokens_used, last_run_at}
GET  logs/                 → [{action, outcome, detail, duration_ms}, ...]
POST run/                  → {result, log_id, duration_ms}
GET  approvals/            → [{context, option_a, option_b, created_at}, ...]
POST approvals/<id>/decide/ → {decision: "approved"|"denied"}
```

**POST /run/ example:**
```json
{
  "messages": [{"role": "user", "content": "Give me a CRM pipeline summary"}],
  "model": "neural-chat"
}
```

**Response:**
```json
{
  "result": "Your pipeline has 14 open deals worth £82,000...",
  "log_id": 47,
  "duration_ms": 2341
}
```

### 5.8 Inbound Webhooks

External platforms can push data to an agent:
```
POST /agents/webhook/<webhook-token>/
Header: X-HMAC-Signature: <hmac-sha256>
```
Verified with HMAC-SHA256 using the `AgentInstance.webhook_token`.

### 5.9 Agent Tools Available

Every agent has access to:

| Tool | Description |
|------|-------------|
| `search_web` | Web search via DuckDuckGo |
| `scrape_website` | Extract content from any URL |
| `call_api` | Make authenticated HTTP requests |

Additionally, agents with hub data access get:

| Agent | Hub Tools |
|-------|----------|
| `crux`, `lead-hunter` | CRM: contacts, deals, pipeline stages |
| `hera`, `nexus` | HR: employees, departments, leave records |
| `cash` | Finance: invoices, payroll records |
| `reporting-bot`, `nova`, `clarity` | All: CRM + HR + Invoice data |

---

## 6. Console Admin — Command Centre

**URL:** `/console/` — requires login.

### 6.1 Main Dashboard

Overview cards: active agents, pending approvals badge, unread notifications, billing status.

### 6.2 AI Agents Overview (`/console/agents/`)

Two sections:
- **Active on Your Business** — hired agents with live status pip and last-run time
- **Available Agents** — grouped by category. Disappears when all agents in a category are hired.

### 6.3 Agent Workspace (`/console/agents/<slug>/`)

Full workspace per agent — chat, log, approvals. Chat history is per session (not persisted between page loads). Logs are permanent.

### 6.4 Hire AI (`/console/hire-ai/`)

Select an agent from the catalogue. Creates an `AgentInstance` linked to the business. Agent is immediately ready to use.

### 6.5 Notifications (`/console/notifications/`)

Bell icon in header shows unread count. All notifications:
- Agent task completions
- Approval requests
- Billing events
- System alerts

Mark all as read via `/console/notifications/mark-read/`.

### 6.6 Billing (`/console/billing/`)

- Current plan and renewal date
- Invoice history with PDF download
- Plan upgrade / downgrade at `/console/billing/plan/`

### 6.7 Security (`/console/security/totp/setup/`)

Enable / disable TOTP two-factor authentication.

### 6.8 Reports (`/console/reports/`)

Daily business intelligence reports. Detail view at `/console/reports/<id>/`.

### 6.9 Platforms (`/console/platforms/`)

Connect social media and external platforms:
- Facebook Pages (Meta Business)
- More platforms in roadmap

---

## 7. UAT Test Cases

**Pre-conditions:** Dev server running on port 1234, Redis + Celery running, LiteLLM proxy or `GROQ_API_KEY` set.

---

### BLOCK A — Authentication

| ID | Test | Steps | Expected Result |
|----|------|-------|----------------|
| A1 | Register | `/accounts/signup/` → fill email + password → submit | Account created, verification email sent |
| A2 | Email verify | Click link in email | Account verified, redirect to login |
| A3 | Login | Valid credentials | Redirect to `/console/` |
| A4 | Rate limit | 5 wrong passwords | Account locked, axes error shown |
| A5 | Social login | Click "Continue with Google" | OAuth redirect, account created/linked |
| A6 | TOTP setup | `/console/security/totp/setup/` → scan QR → enter code | TOTP enabled |
| A7 | TOTP login | Log out → login → enter TOTP code | Access granted |
| A8 | TOTP wrong code | Enter wrong 6-digit code | Access denied, error shown |
| A9 | Logout | Click Logout | Session cleared, redirect to login |

---

### BLOCK B — Business & Module Setup

| ID | Test | Steps | Expected Result |
|----|------|-------|----------------|
| B1 | Create business | `/hub/create/` → fill all fields | Business created at `/hub/<slug>/` |
| B2 | Hub loads | `/hub/<slug>/` as owner | Sidebar shows industry-relevant modules |
| B3 | Activate module | `/console/activate-module/` → select module | Module appears in hub sidebar |
| B4 | Non-employee blocked | Log in as different user, visit `/hub/<slug>/crm/` | 403 or redirect |
| B5 | Invite employee | Hub → Settings → invite by email | Invited user can access the hub |
| B6 | Employee module access | Log in as employee | Only sees activated modules in sidebar |
| B7 | CRM loads | `/hub/<slug>/crm/` | Contact list renders, no errors |
| B8 | Invoicing loads | `/hub/<slug>/invoicing/` | Invoice list renders |
| B9 | HR loads | `/hub/<slug>/hr/` | Employee list renders |
| B10 | Task Board loads | `/hub/<slug>/board/` | Kanban board renders |

---

### BLOCK C — AI Agent — Overview & Hire

| ID | Test | Steps | Expected Result |
|----|------|-------|----------------|
| C1 | Agents overview | `/console/agents/` | Page loads. Active section (empty if none hired). Available agents grouped by category. |
| C2 | No empty categories | Hire all agents in one category, refresh | That category label disappears from Available — no empty `<h6>` header |
| C3 | Hire an agent | Click `+ Hire` on any card | Redirects to hire-ai page, can confirm |
| C4 | Agent appears hired | After C3 | Hired agent appears in "Active on Your Business" with grey pip |
| C5 | Available count updates | After C3 | Subtitle shows updated count |

---

### BLOCK D — Agent Workspace & Chat

| ID | Test | Steps | Expected Result |
|----|------|-------|----------------|
| D1 | Workspace loads | `/console/agents/aria/` | Page renders with chat + log panels |
| D2 | Send message | Type "Hello" → Send | AI response within 30s, no 500 error |
| D3 | Log entry created | After D2 | Log panel shows new entry: action, outcome=success, duration |
| D4 | Web search tool | "Search web for latest AI news" | Agent uses search_web, returns real results |
| D5 | Hub data — CRUX | Hire crux, open workspace, "Show me my pipeline" | Agent reads live CRM data, returns pipeline stats |
| D6 | Hub data — HERA | Hire hera, "How many employees do we have?" | Agent reads live HR data, returns employee count |
| D7 | Hub data — CASH | Hire cash, "What invoices are outstanding?" | Agent reads invoice data |
| D8 | Error handling | Send 5000-character message | Graceful AI error response, no server crash |
| D9 | Multiple agents isolated | Chat with aria then crux | Logs are separate per instance, contexts don't mix |
| D10 | System prompt respected | Each agent introduces itself correctly | Aria acts as support, Crux as CRM manager, etc. |

---

### BLOCK E — Agent API

| ID | Test | Steps | Expected Result |
|----|------|-------|----------------|
| E1 | GET status | `GET /hub/<slug>/agents/aria/api/status/` | JSON: status, tokens_used, last_run_at |
| E2 | GET logs | `GET /hub/<slug>/agents/aria/api/logs/` | JSON array of log entries |
| E3 | POST run | `POST /run/` body: `{"messages":[{"role":"user","content":"Hello"}]}` | JSON: result, log_id, duration_ms |
| E4 | Wrong slug | `POST /hub/wrong-slug/agents/aria/api/run/` | 404 |
| E5 | Non-employee blocked | POST from a non-employee user session | 403 Forbidden |
| E6 | Model override | POST run with `"model": "gpt-4"` | Uses the specified model |

---

### BLOCK F — Approvals & Permissions

| ID | Test | Steps | Expected Result |
|----|------|-------|----------------|
| F1 | Approval request created | Trigger an agent action requiring permission | `AgentPermissionRequest` created, agent status → `waiting` (yellow pip) |
| F2 | Approvals in workspace | Open waiting agent's workspace | Pending approvals panel shows context and options |
| F3 | Approve in workspace | Click Approve | Decision saved, agent → `idle`, Celery resumes task |
| F4 | Deny in workspace | Click Deny | Decision saved, agent → `idle`, action cancelled |
| F5 | Approve via email | Open permission email → click Approve link | `/agents/permission/<id>/respond/` processes approval |
| F6 | Double-response | Try to respond after decision already made | "Already decided" response, not an error |
| F7 | GET approvals API | `GET /hub/<slug>/agents/crux/api/approvals/` | JSON list of pending requests |
| F8 | POST decide API | `POST /approvals/<id>/decide/` `{"decision":"approved"}` | 200 OK, decision recorded |

---

### BLOCK G — Scheduled Tasks (Celery)

| ID | Test | Steps | Expected Result |
|----|------|-------|----------------|
| G1 | Celery connects | `celery -A bengalbound_core worker --loglevel=info` | Worker online, all agent tasks listed |
| G2 | Manual task trigger | `from agents.crux.tasks import live_pipeline_audit; live_pipeline_audit.delay()` | Task runs, AgentLog written |
| G3 | Notification bell | After G2 completes | Header bell shows unread count |
| G4 | Notification content | Open `/console/notifications/` | New entry with agent name, task name, summary |
| G5 | Task failure graceful | Force error (wrong model in settings) | AgentLog outcome=failed, instance remains idle (not stuck `working`) |
| G6 | Dormant contact alert | Run `crux.dormant_contact_alert` | Contacts older than 7 days in active stages → `is_cold=True` |

---

### BLOCK H — Security

| ID | Test | Steps | Expected Result |
|----|------|-------|----------------|
| H1 | CSRF protection | Submit form without CSRF token | 403 Forbidden |
| H2 | Webhook bad HMAC | POST to `/agents/webhook/<token>/` with wrong signature | 403 |
| H3 | Webhook valid HMAC | POST with correct HMAC signature | 200, payload processed |
| H4 | Axes lockout | 5 wrong logins | Locked, lockout message shown |
| H5 | Console unauthenticated | `/console/` while logged out | Redirect to login |
| H6 | Hub unauthenticated | `/hub/<slug>/crm/` while logged out | Redirect to login |
| H7 | API unauthenticated | `POST /hub/<slug>/agents/aria/api/run/` without session | 403 |

---

### BLOCK I — Design & Responsiveness

| ID | Test | Viewport | Expected Result |
|----|------|---------|----------------|
| I1 | Console desktop | 1440px | Glass-morphism sidebar, cards in 3-column grid |
| I2 | Agent cards status pip | Desktop | Green/yellow/grey pip visible, properly coloured |
| I3 | Available agent cards | Desktop | Dimmed icon, `+ Hire` link, grouped by category |
| I4 | No empty headers | All agents hired in a category | Category label removed, not an empty `<h6>` |
| I5 | Workspace mobile | 375px | Chat panel usable, scrollable log panel below |
| I6 | Hub mobile | 375px | Sidebar collapses to hamburger, single-column content |
| I7 | Dark theme | All pages | No hard-coded light backgrounds, all CSS vars used |
| I8 | Toast messages | Submit form | Success/error toast appears and auto-dismisses |
| I9 | Truncation | Long role name in agent card | `text-truncate` applies, no overflow |

---

### BLOCK J — End-to-End Smoke Test (Happy Path)

Run in order. All 15 steps passing = system green.

```
 1. Register at /accounts/signup/
 2. Verify email via link
 3. Log in at /accounts/login/
 4. Create a business: industry=agency at /hub/create/
 5. Visit /hub/<slug>/ — confirm CRM, Invoicing, HR in sidebar
 6. Open /hub/<slug>/crm/ — confirm contacts load
 7. Open /console/agents/ — confirm Available Agents section shows 30 agents
 8. Hire "crux" (CRM Manager)
 9. Hire "hera" (HR Agent)
10. Open /console/agents/crux/ workspace
11. Type: "Hello, introduce yourself" → confirm AI response
12. Type: "Show me my CRM pipeline" → confirm live data returned
13. Open /console/agents/hera/ workspace
14. Type: "How many employees does this business have?" → confirm HR data
15. Check /console/notifications/ — confirm last run appears as a notification
16. Log out → confirm session cleared
```

---

## 8. Quick Reference & Commands

### Start Dev Server

```powershell
python manage.py runserver 0.0.0.0:1234
```

### Seed Everything

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_modules    # 60+ business modules
python manage.py seed_agents     # 30 AI agents in AgentCatalog
```

### Start Celery (required for scheduled tasks)

```powershell
# Worker
celery -A bengalbound_core worker --loglevel=info

# Beat (task scheduler)
celery -A bengalbound_core beat --loglevel=info
```

### Verify AI Pipeline

```powershell
.venv\Scripts\python -c "
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'bengalbound_core.settings.development'
django.setup()
from agents.utils import agent_chat
print(agent_chat([{'role':'user','content':'Say OK in one word'}]))
"
```

### Verify All 30 Agents Import

```powershell
.venv\Scripts\python manage.py shell -c "
from agents.utils import agent_chat, get_llm
from agents.toolkit import get_universal_tools
print('Core AI pipeline: OK')
"
```

### Django System Check

```powershell
python manage.py check --deploy
```

### Key URLs

| Purpose | URL |
|---------|-----|
| Admin panel | `/admin/` |
| Login | `/accounts/login/` |
| Register | `/accounts/signup/` |
| Console | `/console/` |
| Agents overview | `/console/agents/` |
| Hire AI | `/console/hire-ai/` |
| Billing | `/console/billing/` |
| Security (2FA) | `/console/security/totp/setup/` |
| Notifications | `/console/notifications/` |

---

*Last updated: Sprint P3C · 30 AI Agents · LangChain 1.2 / LangGraph · BengalBound HUB v4.2*
