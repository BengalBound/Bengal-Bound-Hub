import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are MediBook, BengalBound's AI Medical Scheduler.

Your role is to ensure zero missed appointments and zero scheduling conflicts. You coordinate patients, providers, and calendars with clinical precision.

Capabilities:
- Generate clinical appointment notes from patient reason and doctor specialty
- Send contextual appointment reminders with preparation instructions
- Suggest reschedule options when conflicts arise
- Flag high-priority patients (urgent symptoms, missed follow-ups)
- Optimise doctor schedules to reduce wait times
- Coordinate multi-provider appointments and referrals

Principles:
- Patient safety is paramount — always flag potential urgent medical needs
- Privacy: never include unnecessary personal health details in communications
- Preparation matters: patients who know what to bring have better outcomes
- No-shows cost the practice — reminder timing is critical (48h + 2h)
- Doctor schedules should be optimised around slot duration, not crammed
- Urgent symptoms (chest pain, difficulty breathing, etc.) trigger immediate escalation

Clinical awareness: flag symptoms that may indicate emergencies. This does not replace clinical judgment.

[STRICT SYSTEM RULES]
1. OUTPUT: Return ONLY raw JSON if requested. NO markdown (```json), NO filler.
2. REASONING: Think step-by-step internally, output final answer only.
3. DOMAIN: Decline out-of-scope tasks. Zero hallucinations.
4. TONE: Professional human employee. Never identify as AI/bot.

"""


class MediBookEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def generate_appointment_notes(self, appointment, instance=None) -> str:
        prompt = f"""Generate pre-consultation notes for this appointment.

Doctor: Dr. {appointment.doctor.name} ({appointment.doctor.specialty})
Patient: {appointment.patient_name}
Visit Reason: {appointment.reason}
Duration: {appointment.duration} minutes
Scheduled: {appointment.scheduled_at}

Generate:
1. Clinical context notes for the doctor (what to be prepared for)
2. Patient preparation instructions (what to bring, what to do before)
3. Any urgency flags based on the reason

Write in clinical but accessible language."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"generate_appointment_notes for appt {appointment.pk}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def reminder_message(self, appointment, hours_before: int, instance=None) -> dict:
        prompt = f"""Write an appointment reminder for {hours_before} hours before the appointment.

Patient: {appointment.patient_name}
Doctor: Dr. {appointment.doctor.name}
Specialty: {appointment.doctor.specialty}
Time: {appointment.scheduled_at}
Reason: {appointment.reason}

Return JSON:
{{
  "sms_text": "short SMS reminder (max 160 chars)",
  "email_subject": "reminder email subject",
  "email_body": "full email body with preparation instructions",
  "urgency": "routine|priority"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"sms_text": f"Reminder: appt with Dr {appointment.doctor.name} at {appointment.scheduled_at}", "email_body": raw, "urgency": "routine"}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"reminder_message for appt {appointment.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def reschedule_suggestion(self, appointment, reason: str, instance=None) -> str:
        prompt = f"""A patient needs to reschedule this appointment.

Patient: {appointment.patient_name}
Original time: {appointment.scheduled_at}
Doctor: Dr. {appointment.doctor.name}
Reason for rescheduling: {reason}
Slot duration needed: {appointment.duration} minutes

Write a professional rescheduling response that:
1. Acknowledges the cancellation
2. Suggests 3 alternative time slots (use relative times like 'next Tuesday at 2pm')
3. Provides a simple way to confirm the new time"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"reschedule_suggestion for appt {appointment.pk}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def triage_urgency(self, reason: str, specialty: str, instance=None) -> dict:
        prompt = f"""Triage the urgency of this medical appointment request.

Reason for visit: {reason}
Doctor specialty: {specialty}

Return JSON:
{{
  "urgency_level": "routine|soon|urgent|emergency",
  "recommended_timeframe": "within X days/hours",
  "red_flags": ["any symptoms that suggest emergency care needed"],
  "triage_notes": "brief clinical triage notes for the reception team"
}}

IMPORTANT: If this indicates a medical emergency, set urgency_level to 'emergency' and clearly state this in red_flags."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"urgency_level": "routine", "recommended_timeframe": "within 1 week", "red_flags": [], "triage_notes": raw}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="triage_urgency",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if res.get("urgency_level") == "emergency":
                raise PermissionRequired(
                    context=f"Emergency medical urgency flagged for reason: '{reason}'. Red flags: {res.get('red_flags')}",
                    option_a="Approve immediately notifying patient to seek emergency care",
                    option_b="Deny (Handle internally)"
                )
        return res
