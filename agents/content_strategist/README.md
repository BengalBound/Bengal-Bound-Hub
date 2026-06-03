# Content Strategist (Serea) — Content Strategy Agent

## Purpose
The Content Strategist is Serea's dedicated content brain. She plans content campaigns, generates draft articles and social posts, maps content to SEO keywords, and keeps the editorial calendar full — acting as a tireless in-house content team.

## Category
Marketing

## Slug
`serea-content`

## Phase
Phase 1 (live)

## Models

| Model | Purpose |
|-------|---------|
| `ContentPiece` | A single piece of content (blog post, social post, email) with draft text, status, and publish date |
| `Campaign` | A content campaign grouping multiple ContentPieces around a theme or launch event |

## Autonomous Tasks

| Task | Schedule | What it does |
|------|----------|--------------|
| Auto-generate drafts | Every 12 hours | Fills the content calendar with AI-drafted pieces based on campaign briefs |
| Campaign strategy | Weekly | Generates a content strategy memo aligned with business goals |
| Weekly digest | Monday 08:30 | Emails a content performance summary to the business owner |

## REST API Endpoints

```
GET  /hub/<slug>/agents/content-strategist/content-pieces/
POST /hub/<slug>/agents/content-strategist/content-pieces/
GET  /hub/<slug>/agents/content-strategist/content-pieces/<pk>/
GET  /hub/<slug>/agents/content-strategist/campaigns/
POST /hub/<slug>/agents/content-strategist/campaigns/
```

## File Structure

```
content_strategist/
  __init__.py
  apps.py
  models.py           ← ContentPiece, Campaign
  serializers.py
  views.py            ← ContentPieceViewSet, CampaignViewSet
  urls.py
  migrations/
  README.md
```

## Related Modules
`website` · `email_marketing` · `announcements`
