# Sylvia (Pitch Presenter) — AI Video Pitch Agent

## Purpose
Sylvia is the AI pitch creator. She takes a business brief, writes a compelling pitch script, generates presentation slides, and hands off to HeyGen to render a professional talking-head video pitch — turning ideas into investor-ready presentations automatically.

## Category
Marketing

## Slug
`sylvia`

## Phase
Phase 1 (live)

## Models

| Model | Purpose |
|-------|---------|
| `VideoPitch` | A video pitch with script, HeyGen video ID, render status, and business link |
| `PresentationSlide` | Individual slide content (title, body, speaker notes) linked to a VideoPitch |

## Autonomous Tasks

| Task | Schedule | What it does |
|------|----------|--------------|
| Poll HeyGen render status | Every 10 minutes | Checks if a queued video render is complete and updates `VideoPitch.status` |

## REST API Endpoints

```
GET  /hub/<slug>/agents/sylvia/pitches/
POST /hub/<slug>/agents/sylvia/pitches/
GET  /hub/<slug>/agents/sylvia/pitches/<pk>/
GET  /hub/<slug>/agents/sylvia/slides/
POST /hub/<slug>/agents/sylvia/slides/
```

## Integration
Requires a HeyGen API key stored in `AgentIntegration` (encrypted). Sylvia calls the HeyGen video generation API after script and slide generation are complete.

## File Structure

```
pitch_presenter/
  __init__.py
  apps.py
  models.py           ← VideoPitch, PresentationSlide
  serializers.py
  views.py            ← VideoPitchViewSet, PresentationSlideViewSet
  urls.py
  migrations/
  README.md
```

## Related Modules
`slides` · `documents`
