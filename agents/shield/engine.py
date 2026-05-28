import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Shield, BengalBound's AI IT Helpdesk Specialist.

Your role is to resolve IT issues fast, build a knowledge base that prevents recurrence, and keep the entire workforce productive. You aim for 80%+ auto-resolution.

Capabilities:
- Diagnose and resolve Tier-1 IT issues automatically
- Search the knowledge base for matching resolutions
- Determine when to escalate vs. self-resolve
- Generate step-by-step resolution guides
- Build knowledge articles from successfully resolved tickets
- Monitor SLA compliance and flag breaches proactively

Principles:
- Attempt auto-resolution first — escalation is a last resort
- Resolution confidence threshold for auto-resolve: >80%
- SLA: critical=1h, high=4h, medium=24h, low=48h
- Knowledge base first: if this was solved before, use that solution
- Plain language: instructions should work for non-technical staff
- Escalate to human when: security incidents, data loss risk, repeated failures, VIP users

Issue categories: hardware, software, network, access, email, other"""


class ShieldEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def resolve_ticket(self, ticket, kb_articles: list = None, instance=None) -> dict:
        kb_context = ""
        if kb_articles:
            kb_context = "\nRelevant KB Articles:\n" + "\n".join(
                f"- [{a.category}] {a.title}: {a.solution[:200]}"
                for a in kb_articles[:3]
            )

        prompt = f"""Diagnose and resolve this IT support ticket.

Title: {ticket.title}
Category: {ticket.category}
Description: {ticket.description}
Priority: {ticket.priority}
Submitted by: {ticket.submitted_by}
{kb_context}

Return JSON:
{{
  "ai_solution": "step-by-step resolution instructions (numbered, plain language)",
  "ai_confidence": float 0-1,
  "should_auto_resolve": boolean (true if confidence >0.8),
  "escalation_reason": "why to escalate (if should_auto_resolve is false)",
  "resolution_category": "hardware|software|network|access|email|other",
  "estimated_fix_time_minutes": integer,
  "kb_article_draft": {{
    "title": "KB article title",
    "problem": "problem description",
    "solution": "solution steps"
  }}
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"ai_solution": raw, "ai_confidence": 0.5, "should_auto_resolve": False, "escalation_reason": "Unable to parse AI response"}
            
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"resolve_ticket for ticket {ticket.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
            
            if ticket.priority == "urgent":
                raise PermissionRequired(
                    context=f"URGENT ticket detected: {ticket.title}. Escalation reason: {res.get('escalation_reason')}",
                    option_a="Approve immediate page to on-call IT",
                    option_b="Deny (Wait for normal SLA)"
                )
        return res

    def sla_assessment(self, ticket, instance=None) -> dict:
        from django.utils import timezone

        sla_hours = {"urgent": 1, "high": 4, "medium": 24, "low": 48}
        age_hours = (timezone.now() - ticket.created_at).total_seconds() / 3600
        sla_limit = sla_hours.get(ticket.priority, 24)
        breached = age_hours > sla_limit
        remaining = max(0, sla_limit - age_hours)

        result = {
            "breached": breached,
            "age_hours": round(age_hours, 1),
            "sla_limit_hours": sla_limit,
            "remaining_hours": round(remaining, 1),
            "urgency": "critical" if breached else ("warning" if remaining < 2 else "ok"),
        }
        
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"sla_assessment for ticket {ticket.pk}",
                outcome='success',
                detail=json.dumps(result),
                model_used="rule-engine",
            )
        return result

    def generate_kb_article(self, ticket, resolution: str, instance=None) -> dict:
        prompt = f"""Create a knowledge base article from this resolved IT ticket.

Issue Title: {ticket.title}
Category: {ticket.category}
Description: {ticket.description}
Resolution Applied: {resolution}

Return JSON:
{{
  "title": "clear, searchable KB article title",
  "category": "{ticket.category}",
  "problem": "clear problem statement that helps future users find this article",
  "solution": "numbered resolution steps with verification step at end",
  "tags": ["searchable tags"]
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"title": ticket.title, "category": ticket.category, "problem": ticket.description, "solution": resolution, "tags": []}
            
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"generate_kb_article for ticket {ticket.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
