# Lead Hunter — B2B Prospector Agent

## Purpose
Lead Hunter is the AI B2B prospector. He discovers qualified leads via web research, scores them by ICP fit, runs multi-step outreach sequences, and delivers weekly pipeline digests — filling the top of the funnel without manual prospecting.

## Category
Sales

## Slug
`lead-hunter`

## Phase
Phase 1 (live)

## Models

| Model | Purpose |
|-------|---------|
| `Prospect` | A discovered B2B lead with company info, ICP score, and contact details |
| `OutreachSequence` | A multi-step email/LinkedIn outreach sequence assigned to a prospect |

## Autonomous Tasks

| Task | Schedule | What it does |
|------|----------|--------------|
| Prospect scoring | Every 4 hours | Re-scores all prospects against the ICP definition |
| Outreach sequences | Every 2 hours | Sends the next step for any active outreach |
| Weekly pipeline digest | Monday 07:30 | Emails a top-of-funnel summary to the business owner |

## REST API Endpoints

```
GET  /hub/<slug>/agents/lead-hunter/prospects/
POST /hub/<slug>/agents/lead-hunter/prospects/
GET  /hub/<slug>/agents/lead-hunter/prospects/<pk>/
GET  /hub/<slug>/agents/lead-hunter/outreach-sequences/
POST /hub/<slug>/agents/lead-hunter/outreach-sequences/
```

## File Structure

```
lead_hunter/
  __init__.py
  apps.py
  models.py           ← Prospect, OutreachSequence
  serializers.py
  views.py            ← ProspectViewSet, OutreachSequenceViewSet
  urls.py
  migrations/
  README.md
```

## Related Modules
`leads` · `crm` · `deal_flow`
