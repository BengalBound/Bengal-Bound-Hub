import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Wrench, BengalBound's AI Home Services Dispatcher.

Your role is to manage field technicians, book plumbing and home service jobs, and ensure parts inventory is adequate for upcoming dispatches.

Capabilities:
- Parse customer requests and classify job urgency and required skills
- Match jobs to available field technicians based on location and schedule
- Identify required inventory parts for a job from a description
- Draft customer confirmation messages and tech briefing notes

Principles:
- Prioritize urgent leaks or outages immediately
- Always verify parts availability before confirming a dispatch
- Keep technician routes optimized
- Output must be professional and clear

Tone: Practical, urgent, and professional.

[STRICT SYSTEM RULES]
1. OUTPUT: Return ONLY raw JSON if requested. NO markdown (```json), NO filler.
2. REASONING: Think step-by-step internally, output final answer only.
3. DOMAIN: Decline out-of-scope tasks. Zero hallucinations.
4. TONE: Professional human employee. Never identify as AI/bot.
"""

class WrenchEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def classify_job(self, request_text: str, instance=None) -> dict:
        prompt = f"""Classify the following customer request for a home service job.

Customer Request:
{request_text}

Return JSON with:
- "job_type": e.g., "plumbing", "electrical", "hvac"
- "urgency": "low", "medium", "high", "emergency"
- "required_skills": list of strings (e.g., ["pipe repair", "welding"])
- "estimated_duration_hours": float
- "required_parts": list of strings (inferred parts needed)"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"job_type": "unknown", "urgency": "low", "required_skills": [], "estimated_duration_hours": 1.0, "required_parts": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="classify_job",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def dispatch_technician(self, job_details: dict, available_techs: list, instance=None) -> dict:
        prompt = f"""Assign the best technician for this job.

Job Details:
{json.dumps(job_details)}

Available Technicians:
{json.dumps(available_techs)}

Return JSON with:
- "assigned_tech_id": string or int
- "reasoning": why this tech was chosen
- "dispatch_notes": instructions for the technician
- "customer_confirmation": a polite message to send to the customer confirming the tech's arrival"""

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
                action="dispatch_technician",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
            
            if job_details.get("urgency") == "emergency":
                raise PermissionRequired(
                    context=f"Emergency dispatch proposed for {res.get('assigned_tech_id')}.",
                    option_a="Approve emergency dispatch",
                    option_b="Review route manually"
                )
        return res
