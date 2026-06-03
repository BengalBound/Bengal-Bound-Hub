# Chloe (Video Concierge) — Live Video AI Agent

## Purpose
Chloe is the AI video host. She manages live WebRTC video sessions, greets visitors with a HeyGen or D-ID avatar, handles pre-meeting qualification, and delivers daily session digests — giving every business a professional video presence without a live receptionist.

## Category
Support & Client Experience

## Slug
`chloe`

## Phase
Phase 1 (live)

## Models

| Model | Purpose |
|-------|---------|
| `VideoSession` | A live or recorded video session with status, duration, visitor info, and WebRTC session ID |

## Autonomous Tasks

| Task | Schedule | What it does |
|------|----------|--------------|
| Daily session digest | 08:00 daily | Emails a summary of yesterday's video sessions to the business owner |
| Session cleanup | Every hour | Marks stale open sessions as timed out |

## REST API Endpoints

```
GET  /hub/<slug>/agents/chloe/sessions/
POST /hub/<slug>/agents/chloe/sessions/
GET  /hub/<slug>/agents/chloe/sessions/<pk>/
```

## Integration
Works with HeyGen / D-ID for avatar rendering and any WebRTC-compatible video infrastructure. Session management is handled via the `video_meet` module.

## File Structure

```
video_concierge/
  __init__.py
  apps.py
  models.py           ← VideoSession
  serializers.py
  views.py            ← VideoSessionViewSet
  urls.py
  migrations/
  README.md
```

## Related Modules
`video_meet` · `booking` · `crm`
