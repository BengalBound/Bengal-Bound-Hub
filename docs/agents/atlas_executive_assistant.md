# Module Requirements: Atlas — AI Executive Assistant
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `atlas` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Google Calendar, Gmail, Google Drive, Notion, Slack

---

## Section 1: Overview

**AI Employee Name:** Atlas | **Department:** Executive Support
**Core Function:** Manages the CEO/director's calendar, prepares meeting briefs, drafts communications, organises documents, and handles scheduling — a full executive assistant operating 24/7.
**Value Prop:** *"Your executive's day runs itself. Atlas handles the admin. You handle the vision."*

---

## Section 2: Core Capabilities

1. **Smart Calendar Management** — Detects scheduling conflicts, suggests optimal meeting slots, blocks focus time automatically
2. **Meeting Brief Generator** — Before every meeting, Gemini prepares a briefing: who's attending, their background, agenda, and suggested talking points
3. **Email Drafting** — Drafts replies to flagged emails matching the executive's writing style and tone
4. **Task Manager** — Captures action items from meetings, emails, and Slack — tracks to completion
5. **Document Organiser** — Auto-files documents in Google Drive by type, client, and date using AI classification
6. **Daily Briefing** — 7am personalised summary: today's schedule, top 3 priority tasks, key emails, and any urgent news
7. **Travel Coordination** — Drafts travel itineraries, compiles hotel/flight options based on preference profile
8. **Expense Tracking** — Logs executive expenses from receipts (photo/email) and generates monthly expense report

---

## Section 3: Django Models

```python
class ExecutiveProfile(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='atlas_executiveprofiles')
    name            = models.CharField(max_length=300)
    timezone        = models.CharField(max_length=50)
    calendar_id     = models.CharField(max_length=300)
    email_address   = models.EmailField()
    writing_tone    = models.CharField(max_length=50, default='professional')
    preferences     = models.JSONField(default=dict)    # Meeting length prefs, travel class, etc.
    focus_hours     = models.JSONField(default=list)    # Blocks to protect e.g. ['09:00-11:00']
    briefing_time   = models.TimeField(default='07:00')

class Task(models.Model):
    PRIORITY = [('low','Low'),('medium','Medium'),('high','High'),('urgent','Urgent')]
    STATUS   = [('open','Open'),('in_progress','In Progress'),('done','Done'),('deferred','Deferred')]
    profile         = models.ForeignKey(ExecutiveProfile, on_delete=models.CASCADE)
    title           = models.CharField(max_length=500)
    description     = models.TextField(blank=True)
    source          = models.CharField(max_length=50)   # 'email','meeting','slack','manual'
    priority        = models.CharField(max_length=10, choices=PRIORITY, default='medium')
    status          = models.CharField(max_length=20, choices=STATUS, default='open')
    due_date        = models.DateField(null=True)
    completed_at    = models.DateTimeField(null=True)
    created_at      = models.DateTimeField(auto_now_add=True)

class MeetingBrief(models.Model):
    profile         = models.ForeignKey(ExecutiveProfile, on_delete=models.CASCADE)
    calendar_event_id = models.CharField(max_length=200)
    meeting_title   = models.CharField(max_length=500)
    scheduled_at    = models.DateTimeField()
    attendees       = models.JSONField(default=list)
    attendee_bios   = models.JSONField(default=dict)    # Gemini-researched backgrounds
    agenda          = models.TextField(blank=True)
    talking_points  = models.JSONField(default=list)
    generated_at    = models.DateTimeField(auto_now_add=True)

class Expense(models.Model):
    CATEGORIES = [('travel','Travel'),('meals','Meals'),('software','Software'),
                  ('marketing','Marketing'),('office','Office'),('other','Other')]
    profile         = models.ForeignKey(ExecutiveProfile, on_delete=models.CASCADE)
    amount          = models.DecimalField(max_digits=12, decimal_places=2)
    currency        = models.CharField(max_length=10, default='BDT')
    category        = models.CharField(max_length=20, choices=CATEGORIES)
    vendor          = models.CharField(max_length=300)
    receipt_file    = models.FileField(upload_to='expenses/', null=True)
    ocr_data        = models.JSONField(default=dict)
    expense_date    = models.DateField()
    logged_at       = models.DateTimeField(auto_now_add=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/atlas/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/profile/` | Executive profile management |
| `GET` | `/calendar/today/` | Today's schedule |
| `POST` | `/calendar/find-slot/` | Find optimal meeting slot |
| `GET` | `/meetings/{id}/brief/` | Pre-meeting brief |
| `GET` | `/tasks/` | Task list (filterable) |
| `POST` | `/tasks/capture/` | Capture task from text/meeting notes |
| `GET` | `/briefing/daily/` | Today's morning briefing |
| `GET/POST` | `/expenses/` | Expense tracking |
| `POST` | `/expenses/upload-receipt/` | OCR receipt + auto-log |
| `GET` | `/expenses/monthly-report/` | Monthly expense summary |

---

## Section 5: Tech Stack & Delivery

```
pip install google-api-python-client google-auth pdfplumber django-apscheduler
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Calendar management, daily briefing, task capture, email drafts | Weeks 1–5 |
| Phase 2 | Meeting brief generator, document organiser, expense tracker | Weeks 6–11 |
| Phase 3 | Slack integration, travel coordination, attendee research, focus time blocking | Weeks 12–16 |

| Tier | Monthly | Features |
|---|---|---|
| Intern | Free | Calendar view + task list |
| Entry | ৳2,000 | Daily briefing, email drafts, scheduling |
| Mid | ৳5,000 | Meeting briefs, expense tracker, task management |
| Senior | ৳10,000 | Full EA suite, Slack, document organiser, travel |

*BengalBound HUB — dev branch*
