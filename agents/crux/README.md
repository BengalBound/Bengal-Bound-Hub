# Crux — CRM Manager Agent

## Purpose
Crux is the AI CRM manager. He scores contacts by engagement, runs follow-up outreach sequences, tracks deal pipeline health, and delivers weekly pipeline reports — turning raw contact data into prioritised revenue actions.

## Category
Sales

## Slug
`crux`

## Phase
Phase 1 (live)

## Models

| Model | Purpose |
|-------|---------|
| `Contact` | CRM contact record with score, status, and business link |
| `Interaction` | Logged touchpoint (call, email, meeting) against a contact |

## Autonomous Tasks

| Task | Schedule | What it does |
|------|----------|--------------|
| Contact scoring | Every 6 hours | Re-scores all contacts based on recent interaction data |
| Follow-up sequences | Every 2 hours | Triggers the next step in any active outreach sequence |
| Weekly pipeline report | Monday 07:00 | Emails a pipeline health digest to the business owner |

## REST API Endpoints

```
GET  /hub/<slug>/agents/crux/contacts/
POST /hub/<slug>/agents/crux/contacts/
GET  /hub/<slug>/agents/crux/contacts/<pk>/
GET  /hub/<slug>/agents/crux/interactions/
POST /hub/<slug>/agents/crux/interactions/
```

## File Structure

```
crux/
  __init__.py
  apps.py
  models.py           ← Contact, Interaction
  serializers.py
  views.py            ← ContactViewSet, InteractionViewSet
  urls.py
  migrations/
  README.md
```

## Related Modules
`crm` · `leads` · `deal_flow` · `invoicing`
