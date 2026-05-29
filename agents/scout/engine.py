import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Scout, BengalBound's AI Competitor Intelligence Analyst.

Your role is to ensure the business is never blindsided by competitor moves. You track changes, assess impact, and translate intelligence into strategic action.

Capabilities:
- Analyse competitor changes for strategic significance and business impact
- Identify patterns in competitor behaviour (pricing cycles, product cadence, hiring signals)
- Generate strategic response recommendations
- Predict competitor moves based on current signals
- Build competitive intelligence summaries for leadership
- Score changes by business impact and urgency

Principles:
- Intelligence without action is useless — always recommend a response
- Separate signal from noise: not every competitor move warrants a reaction
- Look for patterns, not just individual events
- Hiring data is one of the best forward-looking indicators
- Price changes require competitive response analysis within 48 hours
- Context matters: the same action by a leader vs. a follower has different implications

Change types: pricing, product, hiring, ad, content, pr"""


class ScoutEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def analyse_change(self, change, competitor, instance=None) -> dict:
        prompt = f"""Analyse this competitor change for strategic impact.

Competitor: {competitor.name} ({competitor.website})
Change Type: {change.change_type}
Description: {change.description}
Source: {change.source_url or 'Internal report'}

Return JSON:
{{
  "ai_analysis": "3-paragraph strategic impact analysis",
  "impact_level": "low|medium|high",
  "urgency": "monitor|review|act_now",
  "strategic_implications": ["list of implications for our business"],
  "recommended_responses": [
    {{"action": "specific action", "timeline": "when", "owner": "who should own this"}}
  ],
  "pattern_signal": "what this suggests about their strategy",
  "competitor_strength_change": "gaining|stable|losing"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"ai_analysis": raw, "impact_level": change.impact, "urgency": "review", "strategic_implications": [], "recommended_responses": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"analyse_change for {competitor.name}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if res.get("urgency") == "act_now":
                raise PermissionRequired(
                    context=f"URGENT competitor change detected from {competitor.name}: {res.get('ai_analysis')}",
                    option_a="Approve notifying leadership team immediately",
                    option_b="Deny (Wait for weekly digest)"
                )
        return res

    def competitor_profile(self, competitor, instance=None) -> str:
        prompt = f"""Build a competitor intelligence profile.

Competitor: {competitor.name}
Website: {competitor.website}
Pricing URL: {competitor.pricing_url or 'Not available'}
LinkedIn: {competitor.linkedin_url or 'Not available'}
Last Checked: {competitor.last_checked or 'Never'}

Generate a structured competitor profile covering:
1. Business model and positioning
2. Estimated strengths and weaknesses
3. Target customer profile
4. Pricing strategy assessment
5. Growth trajectory signals
6. Our competitive position relative to them"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"competitor_profile for {competitor.name}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def weekly_intel_summary(self, changes: list, competitors: list, instance=None) -> str:
        changes_text = "\n".join(
            f"- [{c.change_type}] {c.competitor.name if hasattr(c, 'competitor') else 'Unknown'}: {c.description[:100]}"
            for c in changes[:10]
        )
        comp_text = ", ".join(c.name for c in competitors[:5])

        prompt = f"""Generate a weekly competitive intelligence summary.

Monitored Competitors: {comp_text}

Changes this week:
{changes_text or 'No significant changes detected'}

Write a concise (1-page) intelligence brief:
1. Most significant competitive development this week
2. Trends across all competitors
3. Our competitive position assessment
4. Top 3 recommended actions this week"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="weekly_intel_summary",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def pricing_response(self, competitor_name: str, their_new_price: str, our_price: str, product: str, instance=None) -> dict:
        prompt = f"""Analyse this competitor pricing move and recommend our response.

Competitor: {competitor_name}
Their new price: {their_new_price}
Our price: {our_price}
Product/Service: {product}

Return JSON:
{{
  "response_recommendation": "hold|match|undercut|premium_position|reframe",
  "rationale": "specific reasoning",
  "messaging_angle": "how to communicate our pricing to market",
  "risk_if_no_action": "what happens if we don't respond",
  "timeline": "how quickly to respond"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"response_recommendation": "hold", "rationale": raw, "messaging_angle": "", "risk_if_no_action": ""}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"pricing_response for {competitor_name}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
