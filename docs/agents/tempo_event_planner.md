# Module Requirements: Tempo — AI Event Planner & Coordinator
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `tempo` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)

---

## Section 1: Overview

**AI Employee Name:** Tempo | **Department:** Operations / Events
**Core Function:** Plans, coordinates, and manages corporate events — from venue research and vendor booking to attendee management, schedule building, and post-event follow-up — without a dedicated event coordinator.
**Value Prop:** *"Every event planned, coordinated, and followed up on — without a single planning meeting."*

---

## Section 2: Core Capabilities

1. **Event Planning Workflow** — Client defines event type, budget, date, and headcount → Tempo builds full event plan
2. **Venue Research** — Researches and shortlists venues based on location, capacity, budget, and requirements
3. **Vendor Coordination** — Manages outreach to caterers, AV teams, photographers, and decorators via email
4. **Attendee Management** — Sends invitations, tracks RSVPs, manages waitlists, sends reminders
5. **Schedule Builder** — Creates detailed run-of-show schedule with time blocks, responsible parties, and contingencies
6. **Budget Tracker** — Tracks spend against budget; alerts on overspend risk
7. **Post-Event Report** — Attendance, feedback survey results, expense summary, improvement recommendations
8. **Calendar Sync** — All event milestones and vendor calls synced to Google Calendar

---

## Section 3: Django Models

```python
class Event(models.Model):
    STATUS = [('planning','Planning'),('confirmed','Confirmed'),('live','Live'),
              ('completed','Completed'),('cancelled','Cancelled')]
    TYPES = [('conference','Conference'),('workshop','Workshop'),('product_launch','Product Launch'),
             ('team_building','Team Building'),('webinar','Webinar'),('gala','Gala/Dinner')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='tempo_events')
    name            = models.CharField(max_length=500)
    event_type      = models.CharField(max_length=30, choices=TYPES)
    date            = models.DateTimeField()
    location        = models.CharField(max_length=500)
    expected_headcount = models.IntegerField()
    total_budget    = models.DecimalField(max_digits=12, decimal_places=2)
    spent_so_far    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status          = models.CharField(max_length=20, choices=STATUS, default='planning')
    ai_plan         = models.TextField(blank=True)     # Gemini-generated event plan
    created_at      = models.DateTimeField(auto_now_add=True)

class Vendor(models.Model):
    CATEGORIES = [('venue','Venue'),('catering','Catering'),('av','AV & Tech'),
                  ('photography','Photography'),('decoration','Decoration'),('transport','Transport')]
    STATUS = [('shortlisted','Shortlisted'),('contacted','Contacted'),('confirmed','Confirmed'),
              ('rejected','Rejected')]
    event           = models.ForeignKey(Event, on_delete=models.CASCADE)
    category        = models.CharField(max_length=20, choices=CATEGORIES)
    name            = models.CharField(max_length=300)
    contact_email   = models.EmailField(blank=True)
    contact_phone   = models.CharField(max_length=30, blank=True)
    quote           = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    status          = models.CharField(max_length=20, choices=STATUS, default='shortlisted')
    notes           = models.TextField(blank=True)

class Attendee(models.Model):
    RSVP = [('pending','Pending'),('confirmed','Confirmed'),('declined','Declined'),('waitlist','Waitlist')]
    event           = models.ForeignKey(Event, on_delete=models.CASCADE)
    name            = models.CharField(max_length=300)
    email           = models.EmailField()
    company         = models.CharField(max_length=300, blank=True)
    rsvp_status     = models.CharField(max_length=20, choices=RSVP, default='pending')
    invitation_sent = models.BooleanField(default=False)
    reminder_sent   = models.BooleanField(default=False)
    attended        = models.BooleanField(null=True)

class RunOfShow(models.Model):
    event           = models.ForeignKey(Event, on_delete=models.CASCADE)
    time_slot       = models.TimeField()
    duration_mins   = models.IntegerField()
    activity        = models.CharField(max_length(500))
    responsible     = models.CharField(max_length(300), blank=True)
    notes           = models.TextField(blank=True)
    order           = models.IntegerField()
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/tempo/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/events/` | Create and manage events |
| `POST` | `/events/{id}/generate-plan/` | AI-generate full event plan |
| `GET` | `/events/{id}/vendors/` | Vendor list + status |
| `POST` | `/events/{id}/vendors/{vid}/contact/` | Send vendor inquiry email |
| `GET` | `/events/{id}/attendees/` | Attendee list + RSVP status |
| `POST` | `/events/{id}/attendees/invite/` | Send invitation batch |
| `POST` | `/events/{id}/attendees/remind/` | Send reminder to pending RSVPs |
| `GET` | `/events/{id}/schedule/` | Run-of-show schedule |
| `GET` | `/events/{id}/budget/` | Budget vs spend tracker |
| `GET` | `/events/{id}/report/` | Post-event summary report |

---

## Section 5: Tech Stack & Delivery

```
pip install reportlab google-api-python-client django-apscheduler requests
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Event creation, AI plan, attendee management, invitation emails | Weeks 1–5 |
| Phase 2 | Vendor management, budget tracker, run-of-show builder | Weeks 6–10 |
| Phase 3 | Calendar sync, post-event report, feedback survey, venue research | Weeks 11–15 |

| Tier | Monthly | Events/mo | Features |
|---|---|---|---|
| Intern | Free | 1 | AI plan + attendee list |
| Entry | ৳2,000 | 3 | Invitations, RSVP tracking, vendors |
| Mid | ৳5,000 | 8 | Budget tracker, run-of-show, calendar |
| Senior | ৳10,000 | Unlimited | Post-event reports, full coordination |

*BengalBound HUB — dev branch*
