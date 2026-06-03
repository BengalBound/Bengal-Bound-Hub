# Scribe — AI Meeting Notetaker Agent

## Purpose
Scribe is the AI meeting notetaker. He connects to video calls via Recall.ai, transcribes conversations in real time, extracts key decisions and action items, and posts structured summaries back into the task board and docs — so no decision ever gets lost.

## Category
Analytics & Intelligence

## Slug
`scribe`

## Phase
Phase 1 (live)

## Models

| Model | Purpose |
|-------|---------|
| `Meeting` | A recorded meeting with transcript, summary, and Recall.ai session ID |
| `ActionItem` | An extracted action item from a meeting, assigned to a person with a due date |

## Autonomous Tasks

| Task | Schedule | What it does |
|------|----------|--------------|
| Process Recall.ai transcripts | Every 15 minutes | Polls for completed transcripts and generates summaries + action items |

## REST API Endpoints

```
GET  /hub/<slug>/agents/scribe/meetings/
POST /hub/<slug>/agents/scribe/meetings/
GET  /hub/<slug>/agents/scribe/meetings/<pk>/
GET  /hub/<slug>/agents/scribe/action-items/
POST /hub/<slug>/agents/scribe/action-items/
```

## Integration
Requires a [Recall.ai](https://recall.ai) API key stored in `AgentIntegration` (encrypted). Scribe joins meetings as a bot and receives webhook callbacks when transcription is complete.

## File Structure

```
scribe/
  __init__.py
  apps.py
  models.py           ← Meeting, ActionItem
  serializers.py
  views.py            ← MeetingViewSet, ActionItemViewSet (via video_concierge router)
  urls.py
  migrations/
  README.md
```

## Related Modules
`video_meet` · `business_calendar` · `task_board` · `docs`
