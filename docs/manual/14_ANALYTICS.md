# Analytics & Intelligence — Module Manual

**Modules covered:** Reports · AI Analytics · AI Assistant · Data Studio · Dashboard Pro · Data Collection · Process Mapper · Call Center

---

## Reports (`/hub/<slug>/reports/`)

Pre-built and scheduled business intelligence reports.

### Report Definitions
Define what a report contains:
- Types: tabular, chart, pivot, KPI, custom
- Sources: CRM, HR, accounting, inventory, sales, custom SQL
- Configurable query and chart settings
- Schedule with cron expression and email recipients

### Report Runs
Each execution stores:
- Status: `running` → `completed` / `failed`
- Result data as JSON, row count
- Run by user, started/completed timestamps

### Dashboards
Assemble multiple reports into a named dashboard layout. Mark as default or share publicly.

**AI Integration:** Hire **Reporting Bot** to auto-generate daily business KPI reports and weekly PDF executive summaries.

---

## AI Analytics (`/hub/<slug>/analytics/`)

Intelligent pattern detection and forecasting.

### Analytics Datasets
- Data sources: CRM, HR, inventory, sales, or other modules
- Schema definition, row count, last refresh timestamp

### AI Insights
Auto-generated insights by type:
- **Trend** — "Sales have grown 23% over the last 30 days"
- **Anomaly** — "Refund rate spiked 3x above average on Tuesday"
- **Forecast** — "At current growth, you'll hit £100k MRR by September"
- **Recommendation** — "Restock SKU-1042 — 3 days of inventory remain"

Each insight has a confidence score and status (new / reviewed / actioned / dismissed).

### KPI Metrics
Named KPIs with: value, target, unit, period, achievement %.

**AI Integration:** Hire **Nova** (data scientist), **Clarity** (feedback trends), **Scout** (competitor monitoring), **Pulse** (market research).

---

## AI Assistant (`/hub/<slug>/assistant/`)

Conversational AI embedded in the hub.

### Conversations
Each user has a persistent conversation history:
- Title and module context (so the assistant understands which area you're asking about)
- Archived flag

### Messages
User/assistant/system message roles, full content, token count, model used.

### Prompt Templates
Reusable prompts per module — administrators define standard prompts for common tasks.

---

## Data Studio (`/hub/<slug>/data/`)

Custom data visualisation and self-service analytics.

### Datasets
Upload or manually enter data (CSV, JSON, or manual input):
- Define columns and row data
- Tag and describe datasets

### Charts
Build visualisations from datasets:
- Types: table, bar, line, pie, scatter, area, pivot
- Configure X axis, Y axis, and grouping
- Filter and chart display options
- Pin to dashboard

### Reports
Assemble charts into named Data Studio reports. Share with team or make public.

---

## Dashboard Pro (`/hub/<slug>/dashboard-pro/`)

Customisable executive dashboard.

### Custom Dashboards
- Named dashboards with slug, icon, colour
- Layout saved as JSON (drag-and-drop grid)
- Mark as default or share with team members

### Widgets
Rich widget types:
- **Stat Card** — single KPI with label and value
- **Bar / Line / Pie Chart** — visualise module data
- **Table / List** — tabular data display
- **Calendar** — upcoming events
- **Map** — geographic data
- **Gauge** — percentage or score
- **Text** — static rich text
- **Activity** — recent system events
- **Quick Links** — shortcuts to hub pages

Each widget has: title, subtitle, config, position, size, and auto-refresh interval.

---

## Data Collection (`/hub/<slug>/data/`)

Mobile-friendly field data collection forms.

### Forms
Collect data from field teams:
- Form types: survey, poll, feedback, intake, inspection, registration
- Anonymous submission option

### Fields
All standard field types: text, number, date, dropdown, checkbox, radio, file upload, rating, yes/no.

### Responses
Each submission stored with respondent name/email, timestamp. Field answers stored individually.

**AI Integration:** Hire **Clarity** to analyse responses and extract themes.

---

## Process Mapper (`/process-mapper/` — suite prefix)

Business process documentation and workflow simulation.

### Process Maps
Version-controlled business process diagrams:
- Status: `draft` → `review` → `approved` → `archived`
- Owner and tag metadata

### Process Steps
Each step in a flow:
- Types: start, end, task, decision, subprocess, delay, approval, notification, system action
- Responsible role or employee
- Estimated duration, SLA, inputs/outputs, tools used

### Process Flows
Connections between steps:
- Types: sequence, yes-branch, no-branch (for decision gateways), exception
- Label for clarity

### Simulation Runs
Run "what-if" simulations on a process:
- Input assumptions
- Results: throughput per day, average cycle time, bottleneck step identified

---

## Call Center (`/hub/<slug>/call-center/`)

Twilio-powered inbound/outbound call management.

### Twilio Configuration
Account SID, auth token, API key, default from number, TwiML app SID — stored securely per business.

### Call Queues
Route inbound calls to agent groups:
- Routing strategies: round robin, simultaneous ring, priority-based
- Hold music and voicemail fallback
- IVR menu integration

### IVR Menus
Interactive voice response trees:
- Welcome message, invalid input response, timeout handling
- Each keypress (0–9, *, #) can: route to queue, play a message, transfer, take voicemail, hang up, or open a sub-menu

### Call Logs
Every call recorded:
- Twilio call SID, caller/called numbers, direction (inbound/outbound)
- Agent who handled, IVR path taken
- Recording URL, call duration, notes
- Linked to CRM contact if matched

### Agent Status
Live availability tracking per agent:
- Statuses: available, on call, wrap-up, break, offline

**AI Integration:** The **Voice Receptionist** agent handles automated call answering, appointment booking, and spam detection — integrating directly with this module.
