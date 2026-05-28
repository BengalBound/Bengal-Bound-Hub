# Phase 2 AI Employees — UI/UX Wireframes

This document details the UI/UX console wireframe specifications for the **Phase 2 AI Employees** inside the Bengal Bound user dashboard.

---

## Screen 1: Lead Hunter Dashboard (`/dashboard/lead-hunter`)
Optimized for cold email sequencing, B2B lead generation, and Prospect list building.

```
+-----------------------------------------------------------------------------------+
|  Lead Hunter — B2B Prospector                                    [Create Campaign] |
+-----------------------------------------------------------------------------------+
|  Lead Search & Enqueue                                                            |
|  Query: [ "Software companies in Dhaka" ]       Target Count: [ 100 ]     [Search] |
+-----------------------------------------------------------------------------------+
|  Active Email Outreach Sequencer                                                  |
|  +-----------------------------------------------------------------------------+  |
|  | Campaign: "Dhaka Tech Agency Cold Outreach"                  Status: Running |  |
|  | - Email Outbox Sync: sales@mycompany.com                                     |  |
|  | - Sequence: Day 1 (Intro) -> Day 3 (Value Prop) -> Day 7 (Followup)          |  |
|  | - Metrics: 142 Sent  |  42 Opened (29%)  |  8 Replies (5.6%)  |  2 Leads     |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
|  Prospect Roster                                                                  |
|  +-----------------------------------------------------------------------------+  |
|  | Prospect: Asif Rahman (CEO, Dhaka Apps)                    Stage: Replied   |  |
|  | Triage Category: Highly Interested / Requesting Demo                        |  |
|  | [View Outbound Thread] [Sync Hubspot] [Pause Sequence]                      |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### Interactions:
- Clicking "Search" calls Lead Hunter's background prospecting engine. Results hydrate the Prospect Roster asynchronously.
- "Sequence" cards expand on tap to expose email template inputs and variable tags (`{first_name}`, `{company}`).

---

## Screen 2: Content Architect Dashboard (`/dashboard/architect`)
Editorial planner, keyword SEO organizer, and structural outline builder.

```
+-----------------------------------------------------------------------------------+
|  Content Architect — SEO Strategist                               [New Brief Plan] |
+-----------------------------------------------------------------------------------+
|  SEO Keyword Planner & Tracker                                                    |
|  +-----------------------------------------------------------------------------+  |
|  | Keyword: "AI Employee Marketplace"                Search Vol: 12.4k / mo     |  |
|  | Difficulty: Medium (42/100)                       Current Position: #8       |  |
|  | Action Plan: Write high-authority comparison blog. [Generate Brief Outline]  |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
|  Editorial Calendar Briefs                                                        |
|  +-----------------------------------------------------------------------------+  |
|  | Topic: "How Compliant AI Employees Are Revolutionizing SMBs"                |  |
|  | Status: Outline Generated                         Target Publish: June 4     |  |
|  | Focus Keywords: compliant AI, digital staff, data privacy                     |  |
|  | [View Generated Brief Outline Drawer] [Send to Serea Copywriter for Drafting] |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### Flow Notes:
- The "Send to Serea" action triggers cross-agent API coordination, generating a pre-filled ContentPiece model for Serea.

---

## Screen 3: Aria Support Console (`/dashboard/aria`)
Customer support ticket visualizer, live FAQ database tuner, and escalation manager.

```
+-----------------------------------------------------------------------------------+
|  Aria — Customer Support Agent                                  [FAQ Setup Tuning] |
+-----------------------------------------------------------------------------------+
|  Support Metrics                                                                  |
|  [ 94% Auto-resolved ]      [ 0.8s Mean Reply Time ]       [ 2 Pending Escales ]  |
+-----------------------------------------------------------------------------------+
|  Incoming Ticket Triage Feed                                                      |
|  +-----------------------------------------------------------------------------+  |
|  | Ticket #ARIA-1048: "Refund request for double billing"     Status: ESCALATED|  |
|  | Client: S. K. Roy (roy@domain.com)                                           |  |
|  | Auto-Draft Response: "Hi Roy, I have queued this with our billing manager...|  |
|  | [Review Auto-Draft] [Approve Send] [Acknowledge Escalation]                  |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## Screen 4: Kai DevOps Console (`/dashboard/kai`)
Server monitor dashboard, Docker statuses, and real-time logs analyzer.

```
+-----------------------------------------------------------------------------------+
|  Kai — DevOps Engineer                                              [SSH Terminal] |
+-----------------------------------------------------------------------------------+
|  Active VPS Performance Metrics                                                   |
|  [ CPU: 24% ]              [ RAM: 74% (11.8/16.0 GB) ]      [ Disk: 48% Used ]    |
+-----------------------------------------------------------------------------------+
|  Docker Containers Status                                                         |
|  - django-api-server    (●) Active  |  Uptime: 14 days     [Restart] [Logs View]  |
|  - postgresql-db        (●) Active  |  Uptime: 14 days     [Restart] [Logs View]  |
|  - local-ollama-ai      (●) Active  |  Uptime: 2 days      [Restart] [Logs View]  |
+-----------------------------------------------------------------------------------+
|  Live System Logs Monitor (Warning Filter)                                        |
|  [18:42:07] WARNING: Throttling org_id 42 -> LiteLLM proxy rate limit threshold hit.|
|  [18:30:12] INFO: Backup database script succeeded. S3 upload finished.          |
+-----------------------------------------------------------------------------------+
```

---

## Screen 5: Hera HR Panel (`/dashboard/hera`)
Leave requests tracker, onboarding checklist runner, and HR contract designer.

```
+-----------------------------------------------------------------------------------+
|  Hera — HR & Employee Directory                                    [Hire Contractor] |
+-----------------------------------------------------------------------------------+
|  Leave Request & Calendar Tracker                                                 |
|  +-----------------------------------------------------------------------------+  |
|  | Employee: Kabir Hossain (Frontend Dev)                  Days: 3 (Maternity) |  |
|  | Period: June 1 - June 3, 2026                           Status: PENDING     |  |
|  | [ Approve Request ]    [ Reject Request ]    [ Ask Kabir for Coverage Info ]|  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
|  Onboarding Checklists                                                            |
|  - New Dev: Rahim (90% complete) -> Pending: NDA signature  [Send Reminder Email]  |
+-----------------------------------------------------------------------------------+
```

---

## Screen 6: Nova Data Analyst (`/dashboard/nova`)
NL-to-SQL dashboard generator, graphical chart builder, and raw CSV exporter.

```
+-----------------------------------------------------------------------------------+
|  Nova — Data Analyst                                                [Export SQLite] |
+-----------------------------------------------------------------------------------+
|  Ask Nova (Natural Language Data Query)                                           |
|  +-----------------------------------------------------------------------------+  |
|  | Question: "Show me monthly subscription revenue from April to June 2026"   |  |
|  +-----------------------------------------------------------------------------+  |
|  Auto-Generated SQL Query:                                                         |
|  "SELECT MONTH(created_at), SUM(amount) FROM billing_subscription GROUP BY..."     |
|  [ Execute Query & Plot ]                                                         |
+-----------------------------------------------------------------------------------+
|  Query Output Plot                                                                |
|                                                                                   |
|    BDT (Thousands)                                                                |
|     15 |                                     *                                    |
|     10 |                      *                                                   |
|      5 |       *                                                                  |
|      0 +-----------------------------------------                                 |
|             April            May            June                                  |
|                                                                                   |
|  [ Download CSV ] [ Save Chart to Overview Dashboard ]                            |
+-----------------------------------------------------------------------------------+
```
