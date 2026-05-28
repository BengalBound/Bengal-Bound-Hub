import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Tempo, BengalBound's AI Events Manager.

Your role is to deliver flawless events — on time, on budget, and above expectations. You plan with military precision and communicate with warmth.

Capabilities:
- Generate complete event run-of-show plans with timelines
- Manage attendee communications (invitations, reminders, follow-ups)
- Track and optimise event budgets
- Coordinate multi-vendor logistics
- Create post-event summaries with ROI analysis
- Handle RSVP management and waitlist coordination

Principles:
- Plan backward from the event date — work in reverse timeline
- Budget buffer: always reserve 10-15% of total budget for unexpected costs
- Attendee experience is the top priority — every friction point costs you engagement
- Communication cadence: invite (6 weeks out), reminder (2 weeks), day-before, day-after thank you
- For B2B events: measure qualified meetings generated, not just attendance
- Document everything: vendors, contracts, contacts, and learnings for the next event

Event types: conference, workshop, product_launch, team_building, webinar, gala"""


class TempoEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def generate_event_plan(self, event, instance=None) -> str:
        budget_used_pct = (float(event.spent_so_far) / float(event.total_budget) * 100) if event.total_budget else 0

        prompt = f"""Generate a complete event plan and run-of-show.

Event: {event.name}
Type: {event.event_type}
Date: {event.date}
Location: {event.location}
Expected Attendees: {event.expected_headcount}
Total Budget: BDT {event.total_budget:,.2f}
Spent So Far: BDT {event.spent_so_far:,.2f} ({budget_used_pct:.0f}%)
Status: {event.status}

Generate:
1. Pre-event checklist (4 weeks out, 2 weeks, 1 week, day before)
2. Day-of run-of-show with hourly timeline
3. Budget breakdown recommendation
4. Key vendor requirements
5. Contingency plans for common issues
6. Success metrics to track"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"generate_event_plan for {event.name}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def attendee_message(self, event, message_type: str, attendees_count: int, instance=None) -> dict:
        message_guides = {
            "invitation": "Warm, exciting, clear value proposition for attending. Include date, location, agenda highlights, registration link.",
            "reminder_2week": "Friendly reminder with logistics (parking, dress code, schedule). Build anticipation.",
            "reminder_1day": "Brief, practical day-before reminder with all logistics, contact number, and what to expect.",
            "thank_you": "Personal thank you. Include key highlights from the event, next steps, and a way to stay connected.",
        }
        guide = message_guides.get(message_type, "Professional event communication")

        prompt = f"""Write an attendee communication for this event.

Event: {event.name}
Type: {event.event_type}
Date: {event.date}
Location: {event.location}
Attendee count: {attendees_count}
Message type: {message_type}

Communication guidance: {guide}

Return JSON:
{{
  "subject": "email subject line",
  "body": "full email body (warm, professional, clear)"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"subject": f"{event.name} — {message_type}", "body": raw}
            
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"attendee_message ({message_type}) for {event.name}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
            
            # Require permission to blast email to attendees
            if attendees_count > 0:
                raise PermissionRequired(
                    context=f"Tempo drafted a {message_type} email for {attendees_count} attendees of {event.name}.\nSubject: {res.get('subject')}",
                    option_a=f"Approve sending email to {attendees_count} attendees",
                    option_b="Deny (Edit manually)"
                )
        return res

    def post_event_summary(self, event, actual_attendance: int, budget_spent: float, instance=None) -> str:
        attendance_rate = (actual_attendance / event.expected_headcount * 100) if event.expected_headcount else 0
        budget_variance = float(event.total_budget) - budget_spent

        prompt = f"""Write a post-event summary and ROI analysis.

Event: {event.name} ({event.event_type})
Date: {event.date}
Location: {event.location}
Expected Attendees: {event.expected_headcount}
Actual Attendance: {actual_attendance} ({attendance_rate:.0f}% of target)
Budget: BDT {event.total_budget:,.2f}
Spent: BDT {budget_spent:,.2f}
Budget Variance: BDT {budget_variance:,.2f} ({'surplus' if budget_variance > 0 else 'overrun'})

Write a structured post-event summary:
1. Event overview and outcomes
2. Attendance and engagement analysis
3. Budget performance
4. Key wins and what went well
5. Improvement areas for next time
6. Recommended follow-up actions"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"post_event_summary for {event.name}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
