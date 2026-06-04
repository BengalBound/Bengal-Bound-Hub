import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Steer, BengalBound's AI Driving Instructor Scheduler.

Your role is to manage driving school bookings, coordinate fleet vehicle availability, and track student progress.

Capabilities:
- Parse student lesson requests (manual vs automatic, time preferences)
- Match students with available instructors and vehicles
- Identify scheduling conflicts or fleet maintenance overlaps
- Draft confirmation messages for students

Principles:
- Ensure no double-booking of vehicles or instructors
- Flag vehicles that are due for maintenance
- Keep instructor routes and schedules optimized
- Output must be professional and encouraging

Tone: Encouraging, organized, and professional.

[STRICT SYSTEM RULES]
1. OUTPUT: Return ONLY raw JSON if requested. NO markdown (```json), NO filler.
2. REASONING: Think step-by-step internally, output final answer only.
3. DOMAIN: Decline out-of-scope tasks. Zero hallucinations.
4. TONE: Professional human employee. Never identify as AI/bot.
"""

class SteerEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def parse_booking_request(self, request_text: str, instance=None) -> dict:
        prompt = f"""Parse the following driving lesson request.

Request:
{request_text}

Return JSON with:
- "vehicle_type": "manual", "automatic", or "any"
- "preferred_times": list of strings (e.g., ["weekend mornings", "monday 3pm"])
- "experience_level": "beginner", "intermediate", "advanced"
- "lesson_duration_hours": float"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"vehicle_type": "any", "preferred_times": [], "experience_level": "beginner", "lesson_duration_hours": 1.0}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="parse_booking_request",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def schedule_lesson(self, booking_details: dict, available_slots: list, instance=None) -> dict:
        prompt = f"""Assign the best instructor and vehicle slot for this lesson.

Booking Details:
{json.dumps(booking_details)}

Available Slots:
{json.dumps(available_slots)}

Return JSON with:
- "assigned_slot_id": string or int
- "reasoning": why this slot was chosen
- "student_confirmation": a polite message to send to the student confirming their lesson"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="schedule_lesson",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
            
        return res
