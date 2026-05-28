# Web Application — UI/UX Wireframes
# (Web (Django templates) — mobile deferred)

This document details the UI/UX wireframe specifications for the **Bengal Bound** web application (Django templates, running in browser on desktop and mobile).

---

## Global Navigation Blueprint (Sticky Bottom Tab Bar)
The web app relies on a responsive navigation bar. High-priority approvals have a floating badge counter.

```
+---------------------------------------------------+
|  [BB Logo] Bengal Bound            [Alerts (3)]   |
+---------------------------------------------------+
|  [================ Offline Banner ===============]  |
+---------------------------------------------------+
|                                                   |
|                Main Viewport Content              |
|                                                   |
+---------------------------------------------------+
|                                                   |
|   [Home]     [Approvals (2)]    [Agents]  [Settings] |
+---------------------------------------------------+
```

### Layout Elements:
1. **Offline Banner:**
   - Automatically slides down from the header bar using a red theme when connectivity is unavailable.
   - Disappears instantly when network states normalize.
2. **Tab Bar:**
   - Minimum height: `56dp`.
   - Text + Icon combinations conforming to touch-target targets (`48x48dp`).

---

## Screen 1: Web Overview Dashboard
Actionable hub providing active status updates and quick toggle keys.

```
+---------------------------------------------------+
|  Welcome back, CEO!                               |
+---------------------------------------------------+
|  Active Vitals Summary                            |
|  +---------------------------------------------+  |
|  |  Agents Hired: 4       |  Compliance: 98%   |  |
|  +---------------------------------------------+  |
+---------------------------------------------------+
|  Active Agent Quick Controls                      |
|  - Concierge (Executive EA)           (●) Running |
|  - Serea (Content Strategist)          (●) Running |
|  - Voice Receptionist (Phone)          (II) Paused|
|                                                   |
|  [ + Hire New Agent ]                             |
+---------------------------------------------------+
```

### Touch Behaviours:
- Tapping an agent name navigates directly to that agent's metric subpage.
- Pausing or running agents triggers immediate optimistic UI changes, followed by backend synchronization.

---

## Screen 2: Real-time Approvals & Compliance Feed
A web-optimized, actionable feed for urgent compliance requests and decisions.

```
+---------------------------------------------------+
|  PENDING ACTIONS                                  |
+---------------------------------------------------+
|                                                   |
|   +-------------------------------------------+   |
|   |  AGENT: Concierge        18:42 - Urgent   |   |
|   |  ACTION: Schedule meeting with investor   |   |
|   |          on external personal calendar?   |   |
|   |                                           |   |
|   |  [REJECT]                     [APPROVE]   |   |
|   +-------------------------------------------+   |
|                                                   |
|   +-------------------------------------------+   |
|   |  AGENT: Serea            18:25 - General  |   |
|   |  ACTION: Publish LinkedIn draft #104      |   |
|   |                                           |   |
|   |  [ View Draft ]    [ Approve ]  [ Reject] |   |
|   +-------------------------------------------+   |
|                                                   |
+---------------------------------------------------+
```

### Interaction:
- Approval actions are one-click buttons with confirmation toasts.
- Real-time feed updates via Django SSE (Server-Sent Events).

---

## Screen 3: Settings & Workspace Configuration
Profile control and team multi-tenancy.

```
+---------------------------------------------------+
|  SETTINGS                                         |
+---------------------------------------------------+
|  User Profile                                     |
|  CEO (ceo@bengalbound.com)                        |
|                                                   |
|  Security                                         |
|  [o] Two-Factor Authentication (MFA)              |
|  [ ] Session timeout (15 min idle)                |
|                                                   |
|  Organization Details                             |
|  Workspace: BengalBound HUB Ltd                   |
|  Plan: Growth Tier                                |
|                                                   |
|  [ Switch Workspace ]                             |
|                                                   |
|  [ Log Out ]                                      |
+---------------------------------------------------+
```
