import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Hera, BengalBound's AI HR Agent.

Your role is to make every employee feel heard, supported, and informed. You handle HR policy questions instantly, manage onboarding seamlessly, and protect employee confidentiality at all times.

Capabilities:
- Answer HR policy questions accurately and empathetically
- Generate personalised onboarding plans for new hires
- Process and assess leave requests
- Draft HR communications (offer letters, warnings, announcements)
- Provide management guidance on difficult HR situations
- Track onboarding progress and flag overdue tasks

Principles:
- Confidentiality is paramount — never share individual data in general responses
- Empathy first: acknowledge the person before answering the policy
- Be precise on policy — vague answers cause more problems than they solve
- Escalate complex situations (harassment, legal risk) to HR leadership
- Onboarding tasks should be specific, dated, and assigned to a responsible party
- Always reference the applicable policy or regulation when answering

HR categories: onboarding, leave, benefits, conduct, payroll, performance, offboarding, compliance

[STRICT SYSTEM RULES]
1. OUTPUT: Return ONLY raw JSON if requested. NO markdown (```json), NO filler.
2. REASONING: Think step-by-step internally, output final answer only.
3. DOMAIN: Decline out-of-scope tasks. Zero hallucinations.
4. TONE: Professional human employee. Never identify as AI/bot.

"""


class HeraEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def answer_policy_query(self, query, instance=None) -> str:
        prompt = f"""Answer this HR policy question accurately and empathetically.

Question: {query.question}
Category: {query.category}

Provide:
1. A clear, direct answer to the question
2. The relevant policy or regulation that applies
3. Any exceptions or edge cases
4. Who to contact if they need further clarification

Be warm but precise. If this involves a legal risk or sensitive situation, recommend escalation."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"answer_policy_query for {query.pk}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def generate_onboarding_plan(self, employee_name: str, role: str, department: str, instance=None) -> list:
        prompt = f"""Create a 30-day onboarding plan for a new employee.

Name: {employee_name}
Role: {role}
Department: {department}

Return a JSON array of onboarding tasks:
{{
  "task": "specific task description",
  "due_days": integer (days from start date),
  "owner": "HR|IT|Manager|Employee",
  "category": "admin|systems|culture|training|intro_meeting"
}}

Cover: admin (contracts, accounts), systems (email, tools), culture (team meetings, handbook), role training."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = []

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="generate_onboarding_plan",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def leave_assessment(self, employee_name: str, leave_type: str, days: int, reason: str, instance=None) -> dict:
        prompt = f"""Assess this leave request.

Employee: {employee_name}
Leave Type: {leave_type}
Duration: {days} days
Reason: {reason}

Return JSON:
{{
  "recommendation": "approve|approve_with_conditions|escalate|deny",
  "policy_basis": "which policy applies",
  "conditions": ["any conditions if approving"],
  "response_to_employee": "draft response message"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"recommendation": "escalate", "policy_basis": raw, "conditions": [], "response_to_employee": ""}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="leave_assessment",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def draft_hr_communication(self, comm_type: str, context: dict, instance=None) -> str:
        context_text = "\n".join(f"{k}: {v}" for k, v in context.items())
        prompt = f"""Draft a professional HR communication.

Type: {comm_type}
Context:
{context_text}

Write a complete, professional HR communication. Be clear, fair, and legally careful. Do not make promises or admissions that could create legal liability."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"draft_hr_communication {comm_type}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if comm_type.lower() in ["termination", "warning", "disciplinary"]:
                raise PermissionRequired(
                    context=f"Sensitive HR communication drafted: {comm_type}. Requires HR Director approval.",
                    option_a="Approve and send",
                    option_b="Deny and schedule meeting"
                )
        return res
