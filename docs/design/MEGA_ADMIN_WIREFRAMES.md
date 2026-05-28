# Mega Admin Panel & Backoffice — UI/UX Wireframes

This document details the UI/UX wireframe specifications for the **Bengal Bound Mega Admin Panel** (located at `/admin/dashboard`). It serves as the unified backoffice for all operational roles in our platform: CEO, CTO, IT Admin, Engineer, and Sales.

---

## Global Workspace View Selector (Top Bar Anchor)
The Mega Admin Panel includes a prominent view switcher in the header, letting operators toggle layouts based on their current focus.

```
+-----------------------------------------------------------------------------------+
|  [BB Logo] MEGA ADMIN  |  Active Workspace: [ CEO/CTO ] [ IT Admin ] [ Engineer ] [ Sales ] |
+------------------------+----------------------------------------------------------+
|  Welcome back, Admin! (Dhaka SOC Center - LIVE)                [Settings] [Sign Out] |
+-----------------------------------------------------------------------------------+
```

---

## Screen 1: CEO / CTO Workspace View
Optimized for high-level business analytics, active MRR indicators, and NGO validations.

```
+-----------------------------------------------------------------------------------+
|  CEO/CTO Executive Dashboard                                       [Export PDF]   |
+-----------------------------------------------------------------------------------+
|  Key Vitals Scoreboard                                                            |
|  [ ৳124,000 MRR (Stripe) ]   [ 42 Active Org Workspaces ]  [ 15 Registered NGOs ] |
+-----------------------------------------------------------------------------------+
|  Stripe Webhooks & Invoice Event Stream                                           |
|  [x] 19:12 - Recieved charge.succeeded for org bengalbound_hub_ltd (৳5,000 BDT)   |
|  [x] 18:45 - Hired agent 'Voice Receptionist' subscription added for client #104   |
+-----------------------------------------------------------------------------------+
|  NGO Free-Tier Review Queue                                                       |
|  +-----------------------------------------------------------------------------+  |
|  | Org: Bangladesh Literacy Foundation (BLF)               Verification: PENDING |  |
|  | Documents: Gov registration PDF attached.                                   |  |
|  | [ Approve Free Licence ]          [ Reject ]         [ Send Query Email ]   |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## Screen 2: IT / Admin System View
Focused on Twilio/SendGrid credentials, Hetzner VPS limits, and team keys.

```
+-----------------------------------------------------------------------------------+
|  IT System Admin & API Configurator                               [Sync Keys]     |
+-----------------------------------------------------------------------------------+
|  Hetzner CX42 VPS Virtual Telemetry                                               |
|  CPU Load: [ ████░░░░░░░░ 34% ]                  RAM Usage: [ ████████░░░░ 64% ]   |
|  Active Volume: 160GB SSD (48% Used)             Uptime: 24 days 12h              |
+-----------------------------------------------------------------------------------+
|  System Integration Key Management                                                |
|  - Twilio Voice Account SID:  [ AC_XXXXXX...      ] (●) Connection: STABLE         |
|  - SendGrid Mail SMTP Key:    [ SG_XXXXXX...      ] (●) Connection: STABLE         |
|  - django-allauth Config:     [ /etc/secrets/...  ] (●) Connection: STABLE         |
+-----------------------------------------------------------------------------------+
|  Staff Invitation Key Generator                                                   |
|  Role: [ Engineer  v ]  Invite Email: [ eng@bengalbound.com ]  [ Generate Link ]   |
+-----------------------------------------------------------------------------------+
```

---

## Screen 3: Engineer Backoffice View
Focuses on prompt override tuning, local logging, and DB schema statistics.

```
+-----------------------------------------------------------------------------------+
|  Engineer Backoffice Console                                         [Run migrations]|
+-----------------------------------------------------------------------------------+
|  Agent Prompt Overrides (On-The-Fly Prompt Tuning)                                |
|  Select Agent: [ Voice Receptionist v ]                                           |
|  System Prompt Instructions:                                                      |
|  +-----------------------------------------------------------------------------+  |
|  | You are Aria, the Voice Receptionist for the user's business. Your main      |  |
|  | task is to greet callers, qualify their intent, screen robocalls, and        |  |
|  | schedule appointments on their integrated calendars.                         |  |
|  +-----------------------------------------------------------------------------+  |
|  [o] Override active system template               [ Save & Deploy Prompt ]       |
+-----------------------------------------------------------------------------------+
|  Live Django Server Logs Analyzer                                                 |
|  [19:12:07] INFO: django-api-server sync user allauth_uid -> sync successful      |
|  [19:10:45] WARNING: compliance.middleware -> Blocked PII email pattern in body   |
+-----------------------------------------------------------------------------------+
```

---

## Screen 4: Sales Portal View
Enables AppSumo license allocations and trial quote overrides.

```
+-----------------------------------------------------------------------------------+
|  Sales Operations & License Manager                                               |
+-----------------------------------------------------------------------------------+
|  AppSumo Campaign Allocations                                                     |
|  +-----------------------------------------------------------------------------+  |
|  | Client Email: client@appsumo.com                                            |  |
|  | Allocated Code: [ SUMO-CODE-1049 ]  Tier: [ Tier 2 - Growth (8 Agents) ]     |  |
|  | [ Allocate License Now ]                                                    |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
|  Manual Customer Trial Override                                                   |
|  Search Client: [ customer@domain.com ]                                           |
|  Extra Trial Days: [ 30 ]  Allowed Requests Count: [ 5000 ]  [ Update Quota ]     |
+-----------------------------------------------------------------------------------+
```
