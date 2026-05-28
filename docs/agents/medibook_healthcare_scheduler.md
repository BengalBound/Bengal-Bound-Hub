# Module Requirements: MediBook — AI Healthcare Scheduler
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `medibook` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Google Calendar, Twilio SMS, WhatsApp Business API, clinic management system webhooks

---

## Section 1: Overview

**AI Employee Name:** MediBook | **Department:** Healthcare
**Target Clients:** Private clinics, dental practices, physiotherapy centers, diagnostic labs, and any healthcare provider with appointment scheduling needs.
**Core Function:** Manages all patient appointment scheduling, sends multi-channel reminders, handles rescheduling and cancellations gracefully, and syncs with existing clinic management systems — reducing no-shows by up to 40%.
**Value Prop:** *"Every patient slot filled. No-shows down 40%. Zero receptionist needed after 5pm."*

| | Human Receptionist | MediBook AI |
|---|---|---|
| Monthly Cost | ৳15,000–৳25,000 | ৳2,000 |
| After-hours booking | ❌ Not available | ✅ 24/7 |
| Reminder channels | Phone calls | SMS + WhatsApp + Email |
| Rescheduling | Manual back-and-forth | Instant self-service |

---

## Section 2: Core Capabilities

1. **Online Booking Portal** — Patients self-book via web widget or WhatsApp bot; real-time slot availability
2. **Multi-Channel Reminders** — Automated reminders: 48 hrs (email), 24 hrs (WhatsApp), 2 hrs (SMS) before appointment
3. **Smart Rescheduling** — Cancellations automatically offer next 3 available slots via WhatsApp/SMS
4. **Waitlist Management** — Cancelled slots instantly notify waitlisted patients; fills automatically
5. **Doctor Availability Management** — Syncs with each doctor's Google Calendar; respects leave and break times
6. **No-Show Tracking** — Logs DNAs (did not attend); auto-blocks repeat no-show patients after threshold
7. **Daily Schedule Brief** — Morning SMS/email to each doctor: today's patient list with appointment details
8. **Post-Visit Follow-Up** — Automated follow-up message after visit for feedback/next appointment

---

## Section 3: Django Models

```python
class Clinic(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='medibook_clinics')
    name            = models.CharField(max_length=300)
    address         = models.TextField()
    phone           = models.CharField(max_length=30)
    timezone        = models.CharField(max_length=50, default='Asia/Dhaka')
    booking_window_days = models.IntegerField(default=30)  # How far ahead patients can book

class Doctor(models.Model):
    clinic          = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    name            = models.CharField(max_length=300)
    specialty       = models.CharField(max_length(200))
    email           = models.EmailField()
    phone           = models.CharField(max_length=30)
    calendar_id     = models.CharField(max_length(300), blank=True)  # Google Calendar ID
    slot_duration   = models.IntegerField(default=20)                # Minutes per appointment
    is_active       = models.BooleanField(default=True)

class Patient(models.Model):
    clinic          = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    name            = models.CharField(max_length=300)
    phone           = models.CharField(max_length=30)
    email           = models.EmailField(blank=True)
    date_of_birth   = models.DateField(null=True, blank=True)
    no_show_count   = models.IntegerField(default=0)
    is_blocked      = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)

class Appointment(models.Model):
    STATUS = [('booked','Booked'),('confirmed','Confirmed'),('cancelled','Cancelled'),
              ('rescheduled','Rescheduled'),('completed','Completed'),('no_show','No Show')]
    patient         = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor          = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    scheduled_at    = models.DateTimeField()
    duration        = models.IntegerField()                           # Minutes
    reason          = models.CharField(max_length(500), blank=True)
    status          = models.CharField(max_length(20), choices=STATUS, default='booked')
    reminder_48h    = models.BooleanField(default=False)
    reminder_24h    = models.BooleanField(default=False)
    reminder_2h     = models.BooleanField(default=False)
    calendar_event  = models.CharField(max_length(200), blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

class Waitlist(models.Model):
    patient         = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor          = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    preferred_dates = models.JSONField(default=list)
    notified        = models.BooleanField(default=False)
    booked          = models.BooleanField(default=False)
    added_at        = models.DateTimeField(auto_now_add=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/medibook/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/clinics/` | Manage clinic profiles |
| `GET/POST` | `/doctors/` | Manage doctors + calendars |
| `GET` | `/slots/{doctor_id}/{date}/` | Available slots for a doctor |
| `POST` | `/appointments/book/` | Book appointment |
| `GET` | `/appointments/` | List appointments (filterable) |
| `PATCH` | `/appointments/{id}/cancel/` | Cancel + offer reschedule |
| `PATCH` | `/appointments/{id}/reschedule/` | Reschedule appointment |
| `POST` | `/appointments/{id}/no-show/` | Mark as no-show |
| `GET` | `/waitlist/` | Manage waitlist |
| `GET` | `/schedule/today/` | Today's schedule per doctor |
| `GET` | `/analytics/` | No-show rate, fill rate, cancellations |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash | ✅ FREE |
| Calendar | Google Calendar API | ✅ FREE |
| SMS | Twilio SMS | 💲 ~$0.008/SMS |
| WhatsApp | WhatsApp Business API | 💲 Per conversation |
| Email | Gmail SMTP | ✅ FREE |
| Task Queue | `django-apscheduler` | ✅ FREE |

```
pip install twilio google-api-python-client google-auth django-apscheduler
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Clinic + doctor setup, manual booking, 24h email reminders, daily schedule email | Weeks 1–6 |
| Phase 2 | WhatsApp bot booking, SMS reminders, waitlist, no-show tracking, Google Calendar sync | Weeks 7–12 |
| Phase 3 | Self-service patient portal, post-visit follow-up, analytics dashboard, clinic management API sync | Weeks 13–20 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | Appointments/mo | Features |
|---|---|---|---|
| Intern | Free | 50 | Manual booking, email reminders |
| Entry | ৳2,000 | 200 | WhatsApp booking, SMS reminders |
| Mid | ৳5,000 | 1,000 | Waitlist, no-show tracking, analytics |
| Senior | ৳10,000 | Unlimited | Multi-doctor, multi-clinic, patient portal |

---
*BengalBound HUB — dev branch*
