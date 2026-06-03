# AI Agents — Complete Manual

BengalBound HUB includes 33 autonomous AI employees. Each agent is a self-contained mini-platform with its own data models, REST API, scheduled Celery tasks, and long-term memory.

---

## How Agents Work

```
User message or scheduled trigger
  → Agent engine reads SYSTEM_PROMPT + tools
  → Calls agent_chat() → LiteLLM proxy → AI model
  → Uses tools: web search, hub data, API calls
  → Takes action or drafts response
  → Writes AgentLog entry
  → If uncertain: raises PermissionRequired → pauses
```

**Three operational modes:**
1. **Chat** — interactive conversation in Console
2. **Scheduled** — autonomous Celery Beat tasks
3. **API** — REST calls from external systems

---

## Hiring an Agent

1. Go to `/console/agents/`
2. Browse Available Agents grouped by category
3. Click **+ Hire** on any agent card
4. Confirm at `/console/hire-ai/`
5. Agent appears in **Active on Your Business** with a status indicator

---

## Agent Status Indicators

| Colour | Status | Meaning |
|--------|--------|---------|
| Green pip | `working` | Running a task right now |
| Yellow pip | `waiting` | Paused — needs approval |
| Grey pip | `idle` | Ready, not running |
| — | `offline` | Deactivated |

---

## Human-in-the-Loop Approval Flow

When an agent needs to take a consequential action:

1. Agent raises `PermissionRequired`
2. Status → `waiting` (yellow pip)
3. Email sent to business owner
4. Owner approves or denies at `/agents/permission/<id>/respond/`
5. **Approved:** `resume_after_approval` Celery task fires, action completes
6. **Denied:** action cancelled, agent returns to `idle`

All decisions are logged in `AgentLog`.

---

## Agent REST API

Standard endpoints for every agent at `/hub/<slug>/agents/<agent-slug>/api/`:

```
GET  status/                → {status, tokens_used, last_run_at}
GET  logs/                  → [{action, outcome, duration_ms, ...}]
POST run/                   → {result, log_id, duration_ms}
GET  approvals/             → [{context, options, created_at}]
POST approvals/<id>/decide/ → {decision: "approved"|"denied"}
```

**Example POST /run/:**
```json
{
  "messages": [{"role": "user", "content": "Summarise my CRM pipeline"}],
  "model": "gemini/gemini-1.5-flash"
}
```

---

## All 33 Agents

### Support & Client Experience

#### Aria — Customer Support
- **Slug:** `aria` | **Category:** Support
- Triages support tickets, drafts empathetic replies, auto-resolves routine issues
- **Scheduled:** Auto-resolve tickets (4hr), SLA breach alerts (30min), daily digest (08:00)
- **Modules:** CRM, Team Chat, Announcements

#### Mira — Customer Success
- **Slug:** `mira` | **Category:** Support
- Monitors client health scores, flags churn risk, sends proactive check-ins
- **Scheduled:** Health score refresh (6hr), churn risk alerts (4hr), weekly digest (Mon 08:00)
- **Modules:** CRM, Invoicing, Reports

#### Concierge — Client Concierge
- **Slug:** `concierge` | **Category:** Operations
- High-touch client journey, VIP communications, meeting scheduling
- **Scheduled:** Daily inbox triage, VIP check-in alerts
- **Modules:** Booking, Business Calendar, CRM

#### Voice Receptionist — Phone AI
- **Slug:** `voice-receptionist` | **Category:** Communication
- Answers inbound calls, books appointments, takes messages, routes to staff
- **Twilio:** `+18664030430` — webhook at `/agents/voice-receptionist/webhook/inbound/`
- **Scheduled:** Appointment reminders (2hr/24hr), spam cleanup, weekly analytics
- **Modules:** Booking, CRM, Business Calendar, Call Center

#### Chloe — Video Concierge
- **Slug:** `chloe` | **Category:** Support
- Manages live WebRTC video sessions, greets visitors with AI avatar
- **Scheduled:** Daily session digest (08:00), stale session cleanup (hourly)
- **Modules:** Video Meet, Booking, CRM

---

### Sales & Revenue

#### Crux — CRM Manager
- **Slug:** `crux` | **Category:** Sales
- Scores contacts, runs follow-up sequences, weekly pipeline reports
- **Scheduled:** Contact scoring (6hr), follow-up sequences (2hr), weekly pipeline report (Mon 07:00)
- **Modules:** CRM, Leads, Deal Flow, Invoicing

#### Lead Hunter — B2B Prospector
- **Slug:** `lead-hunter` | **Category:** Sales
- Discovers qualified B2B leads via web research, runs outreach sequences
- **Scheduled:** Prospect scoring (4hr), outreach sequences (2hr), weekly digest (Mon 07:30)
- **Modules:** Leads, CRM, Deal Flow

---

### Finance & Operations

#### Cash — Payroll Processor
- **Slug:** `cash` | **Category:** Finance
- Audits payroll anomalies, generates payslip summaries, monthly reminders
- **Scheduled:** Monthly payroll reminder (25th of month), anomaly detection (weekly)
- **Modules:** Payroll, HR, Accounting

#### Payload — Procurement Manager
- **Slug:** `payload` | **Category:** Operations
- Vendor assessments, RFQ processing, price benchmarking
- **Scheduled:** Vendor assessments (weekly), stock risk analysis, weekly review
- **Modules:** Inventory, Order Mgmt, Contracts

#### Flux — Supply Chain Manager
- **Slug:** `flux` | **Category:** Operations
- Supply chain health monitoring, supplier risk alerts, inventory analysis
- **Scheduled:** Supplier assessments (weekly), stock risk analysis, weekly report (Mon)
- **Modules:** Inventory, WMS, Order Mgmt, Delivery

#### Reporting Bot — Automated Reporting
- **Slug:** `reporting-bot` | **Category:** Analytics
- Generates daily KPI reports and weekly executive PDF summaries
- **Scheduled:** Daily KPI generation (07:00), weekly executive summary (Mon 06:30)
- **Modules:** Reports, Dashboard Pro, Data Studio

---

### HR & People

#### Hera — HR Agent
- **Slug:** `hera` | **Category:** HR
- Onboarding plans, policy compliance, leave tracking, weekly HR digest
- **Scheduled:** Onboarding plan generation (on hire), leave digest (weekly)
- **Modules:** HR, Payroll, Recruitment, Attendance, Training

#### Nexus — L&D Coordinator
- **Slug:** `nexus` | **Category:** HR
- Skills gap analysis, course recommendations, learning path generation
- **Scheduled:** Course generation (weekly), progress report (Mon)
- **Modules:** LMS, Training, Assessments, HR

---

### Marketing & Content

#### Content Architect — Content Strategist
- **Slug:** `content-architect` | **Category:** Marketing
- Content calendar planning, topic research, SEO optimisation
- **Scheduled:** Content calendar generation (weekly), SEO audit (weekly)
- **Modules:** Website, Email Marketing, Slides

#### Content Strategist (Serea) — AI Content Creator
- **Slug:** `serea-content` | **Category:** Marketing
- AI-generated blog posts, social copy, email sequences, campaign briefs
- **Scheduled:** Draft generation (12hr), campaign strategy (weekly), weekly digest
- **Modules:** Website, Email Marketing, Announcements

#### Oracle — SEO Specialist
- **Slug:** `oracle` | **Category:** Marketing
- SEO audits, keyword research, meta optimisation, competitor gap analysis
- **Scheduled:** Weekly site audit, keyword research, meta tag recommendations
- **Modules:** Website, Email Marketing

#### Luma — Brand & PR
- **Slug:** `luma` | **Category:** Marketing
- Brand monitoring, press release drafting, crisis detection
- **Scheduled:** Crisis monitoring (30min), brand mention alerts, weekly brand digest
- **Modules:** Website, Email Marketing, Announcements

#### Pulse — Market Research
- **Slug:** `pulse` | **Category:** Analytics
- Market trend analysis, industry news digest, weekly market scan
- **Scheduled:** Daily market pulse (08:00), weekly market report (Mon)
- **Modules:** Reports, Data Studio, AI Analytics

#### Sylvia — Pitch Presenter
- **Slug:** `sylvia` | **Category:** Marketing
- Writes pitch scripts, generates slide decks, renders HeyGen video pitches
- **Scheduled:** Poll HeyGen render status (10min)
- **Modules:** Slides, Documents

---

### Analytics & Intelligence

#### Nova — Data Scientist
- **Slug:** `nova` | **Category:** Analytics
- Natural language to SQL queries, anomaly detection, forecasting
- **Scheduled:** Weekly data analysis (Mon), anomaly scan (daily)
- **Modules:** Data Studio, Reports, AI Analytics, Dashboard Pro

#### Clarity — Feedback Analyst
- **Slug:** `clarity` | **Category:** Analytics
- Extracts themes from surveys and reviews, sentiment scoring, insight reports
- **Scheduled:** Theme extraction (weekly), sentiment digest (Mon)
- **Modules:** Forms Builder, Data Collection, Reports

#### Scout — Competitor Intelligence
- **Slug:** `scout` | **Category:** Analytics
- Deep competitor research — pricing, messaging, product changes
- **Scheduled:** Competitor change analysis (daily), weekly intel report (Mon)
- **Modules:** Reports, AI Analytics, Data Studio

#### Scribe — AI Meeting Notetaker
- **Slug:** `scribe` | **Category:** Analytics
- Joins video calls via Recall.ai, transcribes, produces summaries + action items
- **Scheduled:** Process Recall.ai transcripts (15min polling)
- **Modules:** Video Meet, Business Calendar, Task Board, Docs

---

### Technology & IT

#### Kai — DevOps Engineer
- **Slug:** `kai` | **Category:** Technology
- Infrastructure monitoring, incident analysis, deployment summaries
- **Scheduled:** Pipeline health check (30min), incident analysis, daily digest
- **Modules:** Factory Ops, Maintenance

#### Shield — IT Helpdesk
- **Slug:** `shield` | **Category:** Technology
- IT ticket triage, auto-resolve common issues, knowledge base articles
- **Scheduled:** Auto-resolve tickets (4hr), SLA monitoring (30min), KB article generation
- **Modules:** Team Chat

---

### Specialist & Industry

#### Sage — Legal Reviewer
- **Slug:** `sage` | **Category:** Legal
- Contract review, compliance checks, risk flagging
- **Scheduled:** Auto-review queued contracts (4hr), high-risk alerts
- **Modules:** Contracts, Documents

#### Dox — Technical Writer
- **Slug:** `dox` | **Category:** Documents
- SOPs, manuals, API documentation, internal guides
- **Scheduled:** Outdated content scan (weekly), page generation audit
- **Modules:** Docs, Documents, Slides

#### Babel — Translation Specialist
- **Slug:** `babel` | **Category:** Communication
- Translates documents, emails, and announcements to/from any language
- **Scheduled:** Translation queue processing (1hr), retry failed jobs
- **Modules:** Documents, Announcements, Email Marketing

#### Atlas — Executive Assistant
- **Slug:** `atlas` | **Category:** Operations
- Drafts emails, manages schedules, prioritises tasks, writes briefings
- **Scheduled:** Daily morning briefing (07:30), overdue task alerts, weekly summary
- **Modules:** Business Calendar, Task Board, Reports

#### Realt — Real Estate Assistant
- **Slug:** `realt` | **Category:** Real Estate
- Listing generation, client-to-listing matching, market valuation research
- **Scheduled:** Listing performance review (weekly), lead qualification digest
- **Modules:** Property Listings, RE Marketing, RE Client Portal, Booking

#### MediBook — Medical Scheduler
- **Slug:** `medibook` | **Category:** Healthcare
- Appointment reminders, waitlist management, urgency triage
- **Scheduled:** Appointment reminders (1hr before), triage urgency scoring
- **Modules:** Booking, Care Manager, Business Calendar

#### Merch — eCommerce Manager
- **Slug:** `merch` | **Category:** Commerce
- Listing optimisation, reorder checks, competitor price monitoring
- **Scheduled:** Low stock alerts (daily), reorder checks, listing audit (weekly)
- **Modules:** Ecommerce, Inventory, Product Catalog, Store Ops

#### Tempo — Events Manager
- **Slug:** `tempo` | **Category:** Operations
- Event planning, vendor coordination, attendee reminders, RSVP follow-up
- **Scheduled:** Event countdown alerts, RSVP follow-up (48hr before event)
- **Modules:** Booking, Business Calendar, Announcements
