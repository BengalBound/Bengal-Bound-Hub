import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Mira, BengalBound's AI Customer Success Manager.

Your role is to maximise customer lifetime value by ensuring every customer achieves their desired outcomes. You identify churn risks early and intervene with precision.

Capabilities:
- Calculate and interpret customer health scores
- Predict churn probability from engagement signals
- Generate personalised success plans per customer segment
- Draft check-in emails, NPS campaigns, and renewal messages
- Identify upsell and expansion opportunities
- Build onboarding journeys for new customers

Principles:
- Health score is a prediction, not a verdict — use it to guide action, not automate decisions
- Churn signals: declining usage, unresolved tickets, unanswered emails, reduced logins
- The best expansion conversation happens after a success win, not before renewal
- Check-in emails should reference specific value the customer has gotten
- NPS detractors (0-6) need personal outreach within 24 hours
- Every customer interaction should move them closer to their next success milestone

Health score components: login frequency (30%), feature usage (30%), open tickets (20%), engagement (20%)

[STRICT SYSTEM RULES]
1. OUTPUT: Return ONLY raw JSON if requested. NO markdown (```json), NO filler.
2. REASONING: Think step-by-step internally, output final answer only.
3. DOMAIN: Decline out-of-scope tasks. Zero hallucinations.
4. TONE: Professional human employee. Never identify as AI/bot.

"""


class MiraEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def health_assessment(self, client_health, instance=None) -> dict:
        prompt = f"""Assess this customer health record and recommend action.

Health Score: {client_health.health_score}/100
Risk Level: {client_health.risk_level}
Login Frequency: {client_health.login_frequency} times/week
Feature Usage: {client_health.feature_usage}%
Open Tickets: {client_health.open_tickets}
Churn Probability: {client_health.churn_probability or 'Unknown'}%

Return JSON:
{{
  "assessment": "2-paragraph health assessment",
  "churn_risk": "low|medium|high|critical",
  "key_issues": ["specific issues driving the score down"],
  "recommended_actions": ["prioritised list of CS actions"],
  "next_touchpoint": "what the next customer interaction should be",
  "timeline": "how urgent is intervention"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"assessment": raw, "churn_risk": client_health.risk_level, "recommended_actions": [], "key_issues": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"health_assessment for {client_health.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if res.get("churn_risk") == "critical":
                raise PermissionRequired(
                    context=f"CRITICAL churn risk detected for customer. Issues: {', '.join(res.get('key_issues', []))}",
                    option_a="Approve immediate high-priority intervention",
                    option_b="Deny (Handle via standard workflow)"
                )
        return res

    def draft_email(self, business_name: str, email_type: str, context: dict = None, instance=None) -> dict:
        context_text = "\n".join(f"{k}: {v}" for k, v in (context or {}).items())
        email_guides = {
            "onboarding": "Welcome and guide through first value moment. Include 3 quick wins.",
            "checkin": "Reference specific value achieved. Ask about goals. Offer help.",
            "nps": "Ask one simple question. Keep it under 3 sentences. Make it easy to respond.",
            "renewal": "Summarise value delivered. Forward-looking benefits. Make renewal easy.",
            "upsell": "Reference current success. Natural progression to next tier. ROI-focused.",
            "intervention": "Acknowledge inactivity. Express concern. Low-friction re-engagement offer.",
        }
        guide = email_guides.get(email_type, "Professional, value-focused customer email")

        prompt = f"""Draft a customer success email.

Business: {business_name}
Email Type: {email_type}
Context:
{context_text}

Email guidance: {guide}

Return JSON:
{{
  "subject": "email subject line",
  "body": "full email body (professional, warm, action-oriented)"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"subject": f"[{email_type.title()}] {business_name}", "body": raw}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"draft_email {email_type}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def expansion_opportunity(self, client_health, current_plan: str, instance=None) -> dict:
        prompt = f"""Identify expansion opportunity for this customer.

Current Plan: {current_plan}
Health Score: {client_health.health_score}
Feature Usage: {client_health.feature_usage}%
Risk Level: {client_health.risk_level}

Return JSON:
{{
  "ready_for_expansion": boolean,
  "opportunity_type": "upsell|cross_sell|expansion|none",
  "recommended_timing": "when to have this conversation",
  "pitch_angle": "how to frame the expansion conversation",
  "expected_objections": ["likely objections and responses"]
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"ready_for_expansion": False, "opportunity_type": "none", "recommended_timing": raw}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"expansion_opportunity for {client_health.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
