# Client Portal & Console — UI/UX Wireframes

This document details the UI/UX wireframe specifications for the **Bengal Bound** Client Console dashboard. 

---

## Global Layout Structure (Responsive Dashboard)
The dashboard console is structured with a sticky, collapsing sidebar, a contextual header, and a main content viewport.

```
+-----------------------------------------------------------------------------------+
|  [BB Logo]  | Search workspace (Ctrl+K)...                      [Org: BengalBound HUB v]   |
+-------------+---------------------------------------------------------------------+
| (Sidebar)   | (Header)  Overview  /  Active Agents                               |
|             +---------------------------------------------------------------------+
| [Home]      |                                                                     |
| [Agents]    |  [Stat: 4 Active Agents]   [Stat: 98% Health]   [Stat: 14k Requests]|
| [Veritas]   |                                                                     |
| [Billing]   |  +---------------------------------------------------------------+  |
|             |  | Active Agent Roster                                           |  |
| [Agents]    |  | +-----------------------+ +-----------------------+           |  |
|  - Voice    |  | | Concierge             | | Serea                 |           |  |
|  - Serea    |  | | Executive Assistant   | | Content Strategist    |           |  |
|  - Concierge|  | | Running...            | | Running...            |           |  |
|             |  | +-----------------------+ +-----------------------+           |  |
| [Compliance]|  |                                                               |  |
|             |  +---------------------------------------------------------------+  |
| [Settings]  |                                                                     |
+-------------+---------------------------------------------------------------------+
```

### Layout Elements:
1. **Sidebar Navigation:**
   - Navigable items trigger fast state hydration.
   - Sub-menus expand dynamically for configured/hired agents.
2. **Top Header Bar:**
   - Global Search (`Ctrl+K` modal).
   - Organization Switcher dropdown supporting multi-tenancy contexts.

---

## Screen 1: Dashboard Overview (`/dashboard`)
An actionable home screen aggregating company vitals and agent statuses.

```
+-----------------------------------------------------------------------------------+
|  Vitals at a glance                                                               |
|  [ 4 Active Agents ]      [ 98% Inspector Health ]       [ ৳450 Monthly Spend ]   |
+-----------------------------------------------------------------------------------+
|  Live Compliance Activity Feed                                                    |
|  [x] 18:45 - Concierge processed email client validation -> SUCCESS (GDPR compliant)|
|  [!] 18:42 - Serea content generation blocked -> PII Detected -> AUTO-REDACTED     |
|  [x] 18:30 - Voice Receptionist completed call + synced Google Calendar           |
+-----------------------------------------------------------------------------------+
|  Active Agent Summary Cards                                                       |
|  +-----------------------------------+   +-------------------------------------+  |
|  | Concierge              [Active]   |   | Serea                    [Active]   |  |
|  | - Last action: Email triage 3m ago|   | - Last action: Blog draft 12m ago   |  |
|  | - Day volume: 142 emails          |   | - Day volume: 3 posts generated     |  |
|  | [Open Console]                    |   | [Open Console]                      |  |
|  +-----------------------------------+   +-------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## Screen 2: Veritas KYB Onboarding Page (`/dashboard/veritas`)
A multi-step onboarding wizard verifying client identity and generating risk scores.

```
+-----------------------------------------------------------------------------------+
|  Veritas KYB Verification (Step 2 of 3: Document Upload)                           |
|  [1. Business Info] -> [*2. Document Upload*] -> [3. Verification Review]         |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|   Please drag and drop your corporate registration certificates here              |
|   +---------------------------------------------------------------------------+   |
|   |                                                                           |   |
|   |                  [ Drag & Drop PDFs or Images here ]                      |   |
|   |                                 - or -                                    |   |
|   |                            [ Browse Files ]                               |   |
|   |                                                                           |   |
|   +---------------------------------------------------------------------------+   |
|   Accepted formats: PDF, PNG, JPG (Max 10MB)                                      |
|                                                                                   |
|   [ Back ]                                                   [ Next Step ]        |
+-----------------------------------------------------------------------------------+
```

### Flow Rules:
- Document Dropzone provides direct instant OCR parsing feed notifications.
- Step indicators render dynamically based on completed states.

---

## Screen 3: Billing & Subscriptions Portal (`/dashboard/billing`)
Interactive subscription controller and payment connector.

```
+-----------------------------------------------------------------------------------+
|  Billing & Organization Subscriptions                                             |
+-----------------------------------------------------------------------------------+
|  Current Plan: Free Tier (1 active agent, basic compliance)                       |
|                                                                                   |
|  Stripe Billing Controls:                                                         |
|  [ Manage Subscription via Stripe Customer Portal ]                              |
+-----------------------------------------------------------------------------------+
|  Active Subscriptions Details                                                     |
|  - Agent: Concierge (Billing: ৳1,500/month) -> Next renewal: June 23, 2026        |
|  - Agent: Serea     (Billing: ৳1,500/month) -> Next renewal: June 23, 2026        |
|                                                                                   |
|  Estimated June Invoice Total: ৳3,000 BDT                                         |
+-----------------------------------------------------------------------------------+
```

---

## Screen 4: Voice Receptionist Dashboard (`/dashboard/voice`)
Sub-panel for phone call metrics, transcript logs, and appointment rosters.

```
+-----------------------------------------------------------------------------------+
|  Voice Receptionist (Twilio Virtual Phone: +880 123-45678)         [Config Phone] |
+-----------------------------------------------------------------------------------+
|  Call Volumes                                                                     |
|  [ 124 Completed Calls ]     [ 42 Spam/Robocalls Blocked ]   [ 8 Appointments Scheduled]|
+-----------------------------------------------------------------------------------+
|  Live Call Log & Transcriptions                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Client: Rahim Ullah (+880 171-XXXXXX)                     18:32 - Completed |  |
|  | Summary: Inquired about pricing. Scheduled appointment for Tuesday 10:00 AM.|  |
|  | [View Call Recording] [Read Full Transcript Drawer]                         |  |
|  +-----------------------------------------------------------------------------+  |
|  +-----------------------------------------------------------------------------+  |
|  | Unknown Caller                                              18:25 - BLOCKED |  |
|  | Reason: Telemarketing robot pattern identified by LiteLLM proxy Spam Shield.|  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### Full Transcript Drawer Specs:
- Opens as a slide-out right drawer (`width: 400px` on desktop, `100%` on mobile).
- Lists message transcripts highlighting identified calendar parameters.

---

## Screen 5: Serea Copywriter Dashboard (`/dashboard/serea`)
Campaign scheduler and content management panel.

```
+-----------------------------------------------------------------------------------+
|  Serea AI Copywriter                                              [Create Campaign]|
+-----------------------------------------------------------------------------------+
|  Draft Roster                                                                     |
|  +-----------------------------------------------------------------------------+  |
|  | Draft #104: "Why Compliance is your Secret Superpower"       Social: LinkedIn |  |
|  | Content: In today's digital era, global regulations like GDPR are... [Edit] |  |
|  | Status: Ready to post                             [Post Now] [Schedule Post]|  |
|  +-----------------------------------------------------------------------------+  |
|  +-----------------------------------------------------------------------------+  |
|  | Draft #103: "Next-gen AI Employees in Dhaka"                   Social: Blog   |  |
|  | Content: Bengal Bound is bringing autonomous AI staff to...          [Edit] |  |
|  | Status: Draft                                     [Re-generate] [A/B Test]  |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## Screen 6: Concierge Inbox Dashboard (`/dashboard/concierge`)
Triage visualizer, incoming email routing log, and scheduling sync status.

```
+-----------------------------------------------------------------------------------+
|  Concierge Inbox & Assistant                                      [Sync Calendars]|
+-----------------------------------------------------------------------------------+
|  Incoming Emails & Tasks                                                          |
|  +-----------------------------------------------------------------------------+  |
|  | Sender: Karim Ahmed (karim@client.com)                         Priority: HIGH|  |
|  | Triage: Lead Qualification / Meeting Request                                |  |
|  | Action Taken: Auto-replied with calendar booking link. Scheduled sync.      |  |
|  | [View Email Thread] [Acknowledge Triage]                                    |  |
|  +-----------------------------------------------------------------------------+  |
|  +-----------------------------------------------------------------------------+  |
|  | Sender: Spammer (spam@domain.com)                               Priority: LOW |  |
|  | Triage: Spam / General newsletter                                           |  |
|  | Action Taken: Archived. No alerts triggered.                                |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```
