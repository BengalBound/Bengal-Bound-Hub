# Module Requirements: Hera — AI HR Agent
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `hera` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 Google Workspace, Slack, Slack Webhooks, PDF Signer services, Email

---

## Section 1: Overview

**AI Employee Name:** Hera | **Department:** Human Resources
**Core Function:** Automates leave requests, manages contractor and employee onboarding checklists, schedules check-ins, designs HR contracts, and maintains a clean company directory.
**Value Prop:** *"HR checklists run themselves. Contractor onboarding in minutes. Compliance guaranteed."*

| | Human HR Generalist | Hera AI |
|---|---|---|
| Monthly Cost | ৳25,000–৳40,000 | ৳2,000 |
| Checklist Execution | Manual follow-ups | Automated reminders |
| Leave Processing | Slow email back-and-forth | Instant automated routing |
| Contract Creation | Word templates, error-prone | AI-drafted compliant templates |

---

## Section 2: Core Capabilities

1. **Checklist Automation** — Automatically generates onboarding and offboarding checklists for new hires and contractors.
2. **Automated Reminders** — Emails or pings employees when onboarding steps (such as signing an NDA or setting up a bio) are pending.
3. **Leave Request Routing** — Processes holiday and leave applications, checks against department calendar overlap, and handles approval updates.
4. **Contract Drafting** — Uses templates to draft legally compliant employment and independent contractor agreements.
5. **Holiday Calendaring** — Maintains department holiday calendars, ensuring no department is understaffed.
6. **Company Directory** — Keeps employee directory profiles up to date and generates standard org charts.
7. **Performance Check-in Scheduler** — Triggers automated notifications to schedule periodic check-ins.

---

## Section 3: Django Models

```python
from django.db import models
from django.conf import settings

class HeraConfig(models.Model):
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='hera_configs')
    hr_email         = models.EmailField(help_text="Standard mailbox for HR alerts")
    calendar_id      = models.CharField(max_length=300, blank=True)
    is_active        = models.BooleanField(default=True)

class OnboardingChecklist(models.Model):
    STATUS_CHOICES = [('active','Active'),('completed','Completed'),('overdue','Overdue')]
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='hera_checklists')
    employee_name    = models.CharField(max_length=200)
    employee_email   = models.EmailField()
    role_title       = models.CharField(max_length=200)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    checklist_data   = models.JSONField(default=dict, help_text="List of tasks, e.g. {'NDA signed': True, 'Laptop set': False}")
    started_at       = models.DateTimeField(auto_now_add=True)
    completed_at     = models.DateTimeField(null=True, blank=True)

class LeaveRequest(models.Model):
    STATUS_CHOICES = [('pending','Pending'),('approved','Approved'),('rejected','Rejected')]
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='hera_leave_requests')
    employee         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    leave_type       = models.CharField(max_length=50, help_text="e.g. Maternity, Sick, Vacation")
    start_date       = models.DateField()
    end_date         = models.DateField()
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason           = models.TextField(blank=True)
    overlap_checked  = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)

class HRDocumentTemplate(models.Model):
    business         = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='hera_document_templates')
    title            = models.CharField(max_length=200)
    content          = models.TextField(help_text="Markdown or HTML template with placeholds")
    is_active        = models.BooleanField(default=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/hera/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/config/` | View or update Hera's configurations |
| `GET` | `/checklists/` | List all onboarding and offboarding checklists |
| `POST` | `/checklists/` | Create a new onboarding checklist |
| `POST` | `/checklists/{id}/reminder/` | Send reminders for outstanding checklist items |
| `GET` | `/leave/` | View leave requests with calendar overlaps marked |
| `POST` | `/leave/{id}/approve/` | Approve a leave request |
| `POST` | `/leave/{id}/reject/` | Reject a leave request |
| `POST` | `/documents/draft/` | Draft a contract using AI template substitution |
| `GET` | `/analytics/` | Monthly leave stats, checklist completion rate |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| Calendar Integration | Google Calendar API | ✅ FREE |
| Email / Notifications | Django Email + SMTP | ✅ FREE |
| Document PDF Signer | DocuSign REST API or HelloSign | 💲 $25/mo |
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash | ✅ FREE |
| Task Queue | Celery + Redis | ✅ FREE |

```
pip install google-api-python-client requests
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Onboarding checklists, directory view, basic leave requests CRUD | Weeks 1–6 |
| Phase 2 | Overlap calendar checks, automatic email reminders, Slack hook integrations | Weeks 7–12 |
| Phase 3 | AI contract drafting, PDF signing coordination, HR analytics dashboard | Weeks 13–18 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | Employees | Features |
|---|---|---|---|
| Intern | Free | 10 | Onboarding checklists, basic leave tracking |
| Entry | ৳2,000 | 50 | Overlap checks, auto email reminders |
| Mid | ৳5,000 | 250 | PDF signing integration, Slack hooks |
| Senior | ৳10,000 | Unlimited | AI contract drafting, HR analytics, all calendars |

---
*BengalBound HUB — dev branch*
