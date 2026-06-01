# CRM Module — Operations Guide
# BengalBound HUB — BengalBound Ltd
**Version:** 1.0 | **Date:** June 2026 | **Module:** `modules/crm/`

---

## Overview

The BengalBound CRM module (`modules/crm/`) provides a full B2B sales pipeline inside each tenant's hub. It is the primary workspace for the **Crux** AI agent and **Lead Hunter** AI agent.

---

## Data Model

```
Contact
  ├── id, business (FK: BusinessInstance)
  ├── first_name, last_name, email, phone
  ├── company, position, country
  ├── status: lead | prospect | customer | churned
  ├── source: organic | outbound | referral | ad
  └── created_at, updated_at

Deal
  ├── id, business (FK: BusinessInstance)
  ├── contact (FK: Contact)
  ├── title, value (decimal), currency
  ├── stage: discovery | proposal | negotiation | won | lost
  ├── probability (0–100)
  ├── expected_close (date)
  └── owner (FK: User), created_at

Activity
  ├── id, deal (FK: Deal), contact (FK: Contact)
  ├── type: call | email | meeting | note | task
  ├── summary (text)
  ├── completed (bool)
  └── due_date, created_by
```

---

## Pipeline Stages

| Stage | Description | Typical Next Step |
|---|---|---|
| `discovery` | Initial contact made | Send proposal |
| `proposal` | Proposal sent | Follow up |
| `negotiation` | Discussing terms | Close or revise |
| `won` | Deal closed | Onboard to HUB |
| `lost` | Deal not closed | Archive, re-nurture later |

---

## Crux AI Agent Integration

The **Crux** CRM Manager agent automates pipeline hygiene:

- **Stale deal detection:** Flags deals with no activity in 7+ days
- **Data cleaning:** Normalizes contact records, deduplicates emails
- **Pipeline summary:** Weekly digest of deal stages and revenue at risk
- **Next step recommendations:** Suggests best follow-up action per deal

**Trigger:** Crux runs on a daily Celery Beat schedule or on-demand from the console.

**API:** `POST /hub/<slug>/api/agents/crux/tasks/` with task type `pipeline_audit`

---

## Lead Hunter AI Agent Integration

The **Lead Hunter** B2B Prospector sources and qualifies outbound leads:

- Generates ICP-matched prospect lists
- Writes personalized cold email sequences
- Adds qualified leads to CRM as `Contact` records with `source=outbound`
- Tracks email opens and response signals

---

## Access Control

All CRM views use the standard module access pattern:

```python
def contacts_list(request, slug):
    business = get_object_or_404(BusinessInstance, slug=slug)
    employee = get_object_or_404(BusinessEmployee, business=business, user=request.user)
    contacts = Contact.objects.filter(business=business)
    ...
```

Employees with `access_level='viewer'` can read but not create/edit contacts.
Employees with `access_level='manager'` or `access_level='owner'` have full access.

---

## External CRM Syncing

The CRM module supports bidirectional sync with external CRMs:

| External CRM | Status | Sync Method |
|---|---|---|
| HubSpot | Planned | REST API + webhook |
| Salesforce | Planned | REST API |
| Pipedrive | Planned | REST API |
| Zoho CRM | Planned | REST API |

Sync configuration lives in the tenant's module config JSON (`bredbound_tenantmodule.config_json`).

---

## Workspace Admin: CRM Support View

The workspace admin CRM support view (`workspace_admin/crm_support.html`) provides:
- Cross-tenant contact/deal overview for support staff
- Ability to flag contacts for compliance review
- Search across all businesses' CRM data

---

## Key URLs

```
/hub/<slug>/crm/                    — Contact list
/hub/<slug>/crm/contacts/<id>/      — Contact detail
/hub/<slug>/crm/deals/              — Deal pipeline (Kanban)
/hub/<slug>/crm/deals/<id>/         — Deal detail + activity log
/hub/<slug>/api/agents/crux/tasks/  — Crux AI API endpoint
```

---

*BengalBound HUB — CRM Operations Guide v1.0 — June 2026*
