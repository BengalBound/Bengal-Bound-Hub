# Compliance Dashboard — Future UI/UX Wireframes
**Version:** 1.0  
**Date:** 2026-05-25  
**Scope:** Phase 2+ compliance features not yet built

---

## Overview

Current compliance dashboard (`/dashboard/compliance/`) shows three tabs: Audit Log, Violations, Rules.  
This document defines the **next phase** of compliance UI: a proactive, predictive, risk-aware system.

Design rule: every screen must pass the "60-second test" — a non-technical business owner must understand their compliance posture within 60 seconds of opening the page.

---

## Screen 1 — Compliance Command Centre (new default view)

Replaces the current flat tab list. Opens on `/dashboard/compliance/`.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Inspector Command Centre                              [Export PDF] [Settings]│
├──────────────┬──────────────┬──────────────┬──────────────────────────────── │
│ HEALTH SCORE │ RISK LEVEL   │ OPEN CASES   │  LAST AI SCAN                   │
│              │              │              │                                  │
│    92 / 100  │   ● LOW      │     3        │  2 min ago  ✓ Clean             │
│  ████████▒▒  │              │  2 med · 1 hi│                                  │
│  +4 vs last  │              │              │                                  │
│  7 days      │              │              │                                  │
└──────────────┴──────────────┴──────────────┴─────────────────────────────────┘

┌───────────────────────────────┐  ┌─────────────────────────────────────────── ┐
│  7-Day Activity               │  │  Top Triggered Rules (this week)           │
│                               │  │                                             │
│  M  T  W  T  F  S  S         │  │  1. PII_SCAN_EMAIL     ████████████ 28x   │
│  ▓  ▓  ▓  ▓  ░  ░  ░         │  │  2. GDPR_DATA_ACCESS   ████████░░░  19x   │
│  (bar chart — green=ok        │  │  3. RATE_LIMIT_ORG     █████░░░░░░  11x   │
│   red=violations)             │  │  4. CONTENT_POLICY     ████░░░░░░░   8x   │
│                               │  │                                             │
└───────────────────────────────┘  └─────────────────────────────────────────── ┘

┌───────────────────────────────────────────────────────────────────────────────┐
│  Live Violation Feed                                        [View All →]       │
│  ● CRITICAL  Concierge attempted to export raw PII to external URL  2m ago   │
│  ▲ HIGH      Serea generated content with restricted financial claims  1h ago│
│  ◆ MEDIUM    Rate limit exceeded — 5 requests within 10s  3h ago             │
└───────────────────────────────────────────────────────────────────────────────┘
```

**Interactions:**
- Health score ring animates on load (0 → score, 1.2s ease-out)
- Violation feed auto-refreshes every 30s via `GET /api/v1/compliance/violations/?limit=3`
- "Export PDF" generates a 1-page compliance report (backend: `/api/v1/compliance/report/`)
- Risk level chip: click → jumps to Risk Matrix screen

---

## Screen 2 — Violation Detail Drawer (slide-over panel)

Tapping any violation opens a right-side drawer without leaving the page.

```
                                    ┌─────────────────────────────────────┐
                                    │  Violation #VIO-0042                │
                                    │  ─────────────────────────────────  │
                                    │  Severity   ● CRITICAL              │
                                    │  Agent      Concierge               │
                                    │  Action     export_contact_list      │
                                    │  Resource   /api/v1/contacts/export  │
                                    │  Time       2026-05-25 14:32:07 UTC  │
                                    │  Status     OPEN                     │
                                    │                                      │
                                    │  Rules triggered:                    │
                                    │  • PII_EXPORT_BLOCKED                │
                                    │  • GDPR_DATA_PORTABILITY_RESTRICTED  │
                                    │                                      │
                                    │  AI Inspector Reasoning:             │
                                    │  ┌──────────────────────────────┐   │
                                    │  │ "This action would export    │   │
                                    │  │  contact email addresses to  │   │
                                    │  │  an external URL without     │   │
                                    │  │  consent verification.       │   │
                                    │  │  Blocked per GDPR Art. 6."   │   │
                                    │  └──────────────────────────────┘   │
                                    │                                      │
                                    │  [Acknowledge]  [Escalate]  [Audit] │
                                    └─────────────────────────────────────┘
```

**Backend needed:**
- `GET /api/v1/compliance/violations/<id>/` — detail endpoint (ViolationAlert serializer + `inspector_reason`)
- `POST /api/v1/compliance/violations/<id>/escalate/` — sets `severity=CRITICAL`, notifies admin
- Link to "Audit" → opens full audit log filtered by `agent` + `time window`

---

## Screen 3 — Compliance Rules Manager

```
/dashboard/compliance/rules

[+ New Rule]  [Import from Template]  [Bulk Toggle]

┌────────────────────────────────────────────────────────────────────────────┐
│ Filter: [All Regulations ▼]  [All Severity ▼]  [Active Only ✓]  [Search…]  │
└────────────────────────────────────────────────────────────────────────────┘

┌───────┬──────────────────────┬───────────┬───────────┬─────────┬──────────┐
│ Code  │ Rule Name            │ Regulation│ Severity  │ Status  │ Actions  │
├───────┼──────────────────────┼───────────┼───────────┼─────────┼──────────┤
│ PII-01│ Block PII Export     │ GDPR      │ ● CRITICAL│ ● Active│ Edit/Off │
│ PII-02│ Mask Email in Logs   │ GDPR      │ ▲ HIGH    │ ● Active│ Edit/Off │
│ FIN-01│ No Price Guarantees  │ FCA       │ ▲ HIGH    │ ● Active│ Edit/Off │
│ CON-01│ Consent Before Store │ CCPA      │ ◆ MEDIUM  │ ● Active│ Edit/Off │
│ RAT-01│ Rate Limit Enforce   │ Internal  │ ◆ MEDIUM  │ ● Active│ Edit/Off │
└───────┴──────────────────────┴───────────┴───────────┴─────────┴──────────┘
                                                       [← Prev]  [1 2 3]  [Next →]
```

**Rule Edit Drawer:**
```
┌─────────────────────────────────────────────┐
│  Edit Rule — PII-01                         │
│  ─────────────────────────────────────────  │
│  Rule Code      [PII-01          ]          │
│  Name           [Block PII Export]          │
│  Regulation     [GDPR            ▼]         │
│  Severity       [● CRITICAL      ▼]         │
│  Restriction    [Block           ▼]         │
│  Applicable     [EU ✓] [UK ✓] [US ✗]        │
│  Regions        [CA ✗] [AU ✗]               │
│  Active         [● ON]                      │
│                                             │
│  [Cancel]                    [Save Rule]    │
└─────────────────────────────────────────────┘
```

**Backend needed:**
- `POST /api/v1/compliance/rules/` — create rule
- `PATCH /api/v1/compliance/rules/<id>/` — edit/toggle
- `DELETE /api/v1/compliance/rules/<id>/` — delete

---

## Screen 4 — Risk Matrix

```
/dashboard/compliance/risk

        LIKELIHOOD →
         Rare    Unlikely  Possible  Likely  Almost
Impact ↓                                    Certain
─────────────────────────────────────────────────────
Critical │  Med  │  High  │  Crit  │  Crit  │  Crit  │
High     │  Low  │  Med   │  High  │  Crit  │  Crit  │
Medium   │  Low  │  Low   │  Med   │  High  │  Crit  │
Low      │  Low  │  Low   │  Low   │  Med   │  High  │
Minor    │  Low  │  Low   │  Low   │  Low   │  Med   │

● = active risk item plotted on matrix (from live violations)
```

Each cell is colour-coded (green/yellow/orange/red). Hover a cell → tooltip lists the violations in that quadrant.

**Backend needed:**
- Extend `ViolationAlert` model with `likelihood` field (low/medium/high/critical)
- `GET /api/v1/compliance/risk-matrix/` — returns grouped violations by `(severity, likelihood)` bucket

---

## Screen 5 — Compliance Report Export

Triggered from Command Centre → "Export PDF". Opens a modal:

```
┌──────────────────────────────────────────────────────┐
│  Generate Compliance Report                          │
│  ──────────────────────────────────────────────────  │
│  Period    [Last 7 days ▼]                           │
│  Format    [● PDF]  [○ CSV]  [○ JSON]                │
│  Include   [✓] Executive Summary                     │
│            [✓] Violation Log                         │
│            [✓] Audit Trail                           │
│            [✓] Rule Coverage Map                     │
│            [○] Raw Event Data                        │
│                                                      │
│  [Cancel]                    [Generate & Download]   │
└──────────────────────────────────────────────────────┘
```

**PDF report layout:**
```
Page 1 — Executive Summary
  • Overall health score + trend
  • #violations by severity
  • Top 3 risk areas

Page 2 — Violation Log (tabular)
  • Timestamp, Agent, Action, Rule, Status, Resolution

Page 3 — Audit Trail
  • All BLOCKED/REQUIRES_APPROVAL events

Page 4 — Rule Coverage
  • Active rules vs total defined
  • Regulations covered: GDPR ✓  CCPA ✓  FCA ●  ISO-27001 ○
```

**Backend needed:**
- `POST /api/v1/compliance/report/` — accepts `{period, format, sections[]}`
- Returns `{ report_url: "..." }` (temp S3/local file URL)

---

## Screen 6 — Regulatory Radar (new tab)

Track changes in global regulations affecting the platform.

```
/dashboard/compliance/regulations

┌──────────────────────────────────────────────────────────────────────────── ┐
│  Regulatory Radar                                                            │
│  Regulations your organisation is exposed to based on user countries        │
├──────────────────────────────────────────────────────────────────────────── ┤
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────────┐│
│  │ GDPR                │  │ CCPA                │  │ UK GDPR              ││
│  │ EU · Active         │  │ California · Active  │  │ UK · Active          ││
│  │ ● COMPLIANT         │  │ ● COMPLIANT          │  │ ● COMPLIANT          ││
│  │ 14/15 rules active  │  │ 6/8 rules active     │  │ 11/12 rules active   ││
│  └─────────────────────┘  └─────────────────────┘  └──────────────────────┘│
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────────┐│
│  │ FCA                 │  │ ISO 27001           │  │ SOC 2                ││
│  │ UK · Partial        │  │ Global · Not Set Up  │  │ US · Not Set Up      ││
│  │ ▲ PARTIAL           │  │ ○ NOT CONFIGURED     │  │ ○ NOT CONFIGURED     ││
│  │ 2/5 rules active    │  │ [+ Configure]        │  │ [+ Configure]        ││
│  └─────────────────────┘  └─────────────────────┘  └──────────────────────┘│
└──────────────────────────────────────────────────────────────────────────── ┘
```

**Data model additions:**
- `Regulation` model: `code`, `name`, `jurisdiction`, `description`, `is_enabled`
- Link `ComplianceRule.regulation` FK → `Regulation`
- Pre-seed: GDPR, CCPA, UK GDPR, FCA, ISO-27001, SOC2, HIPAA, PCI-DSS

---

## Mobile Compliance Screens

### Mobile — Violations Feed (compact)

```
┌─────────────────────────────┐
│ ← Inspector         [Filter]│
├─────────────────────────────┤
│  HEALTH SCORE      92/100   │
│  ████████████░░  ● LOW RISK │
├─────────────────────────────┤
│ ● Concierge PII export      │
│   CRITICAL · 2m ago     →  │
│ ▲ Serea financial claim     │
│   HIGH · 1h ago         →  │
│ ◆ Rate limit exceeded       │
│   MEDIUM · 3h ago       →  │
│ ✓ Nova data query allowed   │
│   ALLOWED · 4h ago      →  │
└─────────────────────────────┘
```

### Mobile — Violation Detail (full screen)

```
┌─────────────────────────────┐
│ ← Violation #VIO-0042       │
├─────────────────────────────┤
│ ● CRITICAL                  │
│ Concierge                   │
│ export_contact_list         │
├─────────────────────────────┤
│ Inspector says:             │
│ "This action would export   │
│  contact emails without     │
│  consent. GDPR Art. 6."    │
├─────────────────────────────┤
│ Rules triggered:            │
│ • PII_EXPORT_BLOCKED        │
│ • GDPR_DATA_PORTABILITY     │
├─────────────────────────────┤
│ [Acknowledge] [Escalate]    │
└─────────────────────────────┘
```

---

## Implementation Priority

| Feature                   | Sprint | Backend needed                                   | Frontend          |
|---------------------------|--------|--------------------------------------------------|-------------------|
| Health score widget       | P1     | Analytics endpoint aggregate                     | Command Centre    |
| Violation detail drawer   | P1     | `GET /violations/<id>/`                          | Slide-over panel  |
| Rules CRUD                | P1     | `POST/PATCH/DELETE /compliance/rules/`           | Rules Manager     |
| Risk matrix               | P2     | `likelihood` field + `/risk-matrix/` endpoint    | Matrix grid       |
| PDF report export         | P2     | `/compliance/report/` PDF gen (ReportLab/WeasyPrint) | Modal + DL  |
| Regulatory Radar          | P3     | `Regulation` model + seed data                   | Cards grid        |
| Real-time WebSocket feed  | P3     | Django Channels consumer for violations           | Live feed banner  |

---

## Design Tokens (reuse from existing `AppColors` / Tailwind)

| Token          | Value      | Usage                    |
|----------------|------------|--------------------------|
| `--risk-crit`  | `#EF4444`  | CRITICAL severity        |
| `--risk-high`  | `#F97316`  | HIGH severity            |
| `--risk-med`   | `--warning`| MEDIUM severity          |
| `--risk-low`   | `--success`| LOW severity / ALLOWED   |
| `--health-bg`  | surface    | Score ring background    |
| `--health-fill`| accent     | Score ring fill          |
