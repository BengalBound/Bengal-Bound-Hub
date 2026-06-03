# Aria — Customer Support Agent

## Purpose
Aria is the AI customer support specialist. She triages inbound support tickets, drafts empathetic replies, auto-resolves routine issues, sends SLA breach alerts, and delivers daily digest emails — keeping customer satisfaction high without a large support headcount.

## Category
Support

## Slug
`aria`

## Phase
Phase 1 (live)

## Models

| Model | Purpose |
|-------|---------|
| `SupportTicket` | Inbound support request with subject, description, channel, priority, status |
| `TicketResponse` | Drafted reply (AI-generated or human override) linked to a ticket |

## Autonomous Tasks

| Task | Schedule | What it does |
|------|----------|--------------|
| Auto-resolve tickets | Every 4 hours | Closes tickets in `open` state older than the SLA threshold |
| SLA breach alerts | Every 30 minutes | Flags tickets about to breach SLA and notifies the team |
| Daily digest | 08:00 daily | Emails a support summary to the business owner |

## REST API Endpoints

```
GET  /hub/<slug>/agents/aria/tickets/
POST /hub/<slug>/agents/aria/tickets/
GET  /hub/<slug>/agents/aria/tickets/<pk>/
POST /hub/<slug>/agents/aria/tickets/<pk>/suggest-response/   ← AI drafts a reply
GET  /hub/<slug>/agents/aria/responses/
POST /hub/<slug>/agents/aria/responses/
```

## File Structure

```
aria/
  __init__.py
  apps.py
  models.py           ← SupportTicket, TicketResponse
  serializers.py
  views.py            ← SupportTicketViewSet, TicketResponseViewSet
  urls.py
  migrations/
  README.md
```

## Related Modules
`crm` · `team_chat` · `announcements`
