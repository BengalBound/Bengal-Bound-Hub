# Mira — Customer Success Agent

## Purpose
Mira is the AI customer success manager. She monitors client health scores, flags churn risk early, sends proactive check-in emails, and delivers weekly success digests — helping businesses retain customers without manual effort.

## Category
Support

## Slug
`mira`

## Phase
Phase 1 (live)

## Models

| Model | Purpose |
|-------|---------|
| `ClientHealth` | Health score record for a client — tracks engagement, NPS, usage signals |
| `SuccessEmail` | Outgoing success email (AI-drafted or human-edited) sent to a client |

## Autonomous Tasks

| Task | Schedule | What it does |
|------|----------|--------------|
| Health score refresh | Every 6 hours | Recalculates health scores for all active clients |
| Churn risk alerts | Every 4 hours | Flags clients whose health score dropped below threshold |
| Weekly digest | Monday 08:00 | Emails a customer success summary to the business owner |

## REST API Endpoints

```
GET  /hub/<slug>/agents/mira/client-health/
POST /hub/<slug>/agents/mira/client-health/
GET  /hub/<slug>/agents/mira/client-health/<pk>/
GET  /hub/<slug>/agents/mira/success-emails/
POST /hub/<slug>/agents/mira/success-emails/
```

## File Structure

```
mira/
  __init__.py
  apps.py
  models.py           ← ClientHealth, SuccessEmail
  serializers.py
  views.py            ← ClientHealthViewSet, SuccessEmailViewSet
  urls.py
  migrations/
  README.md
```

## Related Modules
`crm` · `invoicing` · `reports`
