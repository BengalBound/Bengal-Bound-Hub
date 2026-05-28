import json
from agents.utils import agent_chat

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

    def resolve_ticket(self, ticket, kb_articles: list = None) -> dict:
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
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"ai_solution": raw, "ai_confidence": 0.5, "should_auto_resolve": False, "escalation_reason": "Unable to parse AI response"}

    def sla_assessment(self, ticket) -> dict:
        from django.utils import timezone

        sla_hours = {"urgent": 1, "high": 4, "medium": 24, "low": 48}
        age_hours = (timezone.now() - ticket.created_at).total_seconds() / 3600
        sla_limit = sla_hours.get(ticket.priority, 24)
        breached = age_hours > sla_limit
        remaining = max(0, sla_limit - age_hours)

        return {
            "breached": breached,
            "age_hours": round(age_hours, 1),
            "sla_limit_hours": sla_limit,
            "remaining_hours": round(remaining, 1),
            "urgency": "critical" if breached else ("warning" if remaining < 2 else "ok"),
        }

    def generate_kb_article(self, ticket, resolution: str) -> dict:
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
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"title": ticket.title, "category": ticket.category, "problem": ticket.description, "solution": resolution, "tags": []}
