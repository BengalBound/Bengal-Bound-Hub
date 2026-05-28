import json
from agents.utils import agent_chat

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

HR categories: onboarding, leave, benefits, conduct, payroll, performance, offboarding, compliance"""


class HeraEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def answer_policy_query(self, query) -> str:
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
        return agent_chat(messages)

    def generate_onboarding_plan(self, employee_name: str, role: str, department: str) -> list:
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
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    def leave_assessment(self, employee_name: str, leave_type: str, days: int, reason: str) -> dict:
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
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"recommendation": "escalate", "policy_basis": raw, "conditions": [], "response_to_employee": ""}

    def draft_hr_communication(self, comm_type: str, context: dict) -> str:
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
        return agent_chat(messages)
