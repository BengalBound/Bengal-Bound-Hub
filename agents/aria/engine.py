import json
from agents.utils import agent_chat

SYSTEM_PROMPT = """You are Aria, BengalBound's AI Customer Support Specialist.

Your role is to resolve customer issues with empathy, accuracy, and speed. You operate 24/7 and hold yourself to strict SLA standards.

Capabilities:
- Diagnose customer problems from ticket descriptions
- Generate clear, empathetic, solution-focused replies
- Score urgency and recommend priority escalation
- Draft follow-up messages for unresolved tickets
- Build resolution summaries for the knowledge base

Principles:
- Always acknowledge the customer's frustration before solving
- Provide step-by-step solutions, never vague answers
- If unsure, escalate rather than guess
- Keep replies concise and jargon-free unless the customer is technical
- End every response with a clear next step or call to action

Tone: Warm, professional, solution-focused. Never dismissive."""

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b


class AriaEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def resolve_ticket(self, ticket, instance=None) -> dict:
        prompt = f"""A customer has submitted a support ticket. Provide a resolution.

Ticket Subject: {ticket.subject}
Description: {ticket.description}
Channel: {ticket.channel}
Priority: {ticket.priority}

Return a JSON object with:
- "resolution": step-by-step resolution instructions
- "customer_reply": the reply to send the customer (warm, clear, actionable)
- "confidence": float 0-1 (how confident you are this resolves it)
- "escalate": boolean (true if human agent needed)
- "resolution_category": one of [billing, technical, account, product, policy, other]"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = {"customer_reply": raw, "confidence": 0.7, "escalate": False, "resolution_category": "other"}

        if result.get("confidence", 0) < 0.8:
            raise PermissionRequired(
                context=f"I want to send this reply to ticket #{ticket.pk} but my confidence is only {result.get('confidence', 0)}.",
                option_a="Approve and send the reply.",
                option_b="Deny and assign to a human agent."
            )

        if instance:
            from agents.models import AgentLog
            from django.conf import settings
            AgentLog.objects.create(
                instance=instance,
                action=f"resolve_ticket #{ticket.pk}",
                outcome='success' if not result.get('escalate') else 'escalated',
                detail=json.dumps(result),
                model_used=getattr(settings, 'SEREA_TASK_MODELS', {}).get('chat', 'gpt-4'),
            )
            
        return result

    def draft_reply(self, ticket, customer_sentiment: str = "neutral") -> str:
        prompt = f"""Draft a customer support reply for this ticket.

Subject: {ticket.subject}
Issue: {ticket.description}
Customer Sentiment: {customer_sentiment}
Priority: {ticket.priority}

Write ONLY the email/chat reply body — empathetic opening, clear solution, next steps."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return agent_chat(messages)

    def escalation_advice(self, ticket) -> str:
        prompt = f"""A support ticket needs escalation assessment.

Subject: {ticket.subject}
Description: {ticket.description}
Priority: {ticket.priority}

Provide:
1. Why this should/should not escalate to a human
2. Which team should handle it (billing / engineering / account management / senior support)
3. Key context to hand off to the human agent"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return agent_chat(messages)

    def generate_kb_article(self, ticket, resolution: str) -> dict:
        prompt = f"""Based on this resolved support ticket, create a knowledge base article.

Subject: {ticket.subject}
Issue: {ticket.description}
Resolution: {resolution}

Return JSON with:
- "title": KB article title
- "problem": clear problem statement
- "solution": numbered resolution steps
- "tags": list of relevant tags"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"title": ticket.subject, "problem": ticket.description, "solution": resolution, "tags": []}
