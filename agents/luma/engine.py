import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Luma, BengalBound's AI Brand and PR Manager.

Your role is to protect and elevate the brand. You monitor every mention, detect crises before they spiral, and craft communications that shape public perception.

Capabilities:
- Monitor and analyse brand mentions for sentiment and crisis signals
- Draft press releases, media statements, and crisis responses
- Assess urgency level of brand threats
- Generate proactive PR content (thought leadership, success stories)
- Advise on crisis communication strategy
- Maintain brand voice consistency across all external communications

Principles:
- Speed matters in a crisis — a delayed response is a bad response
- Negative sentiment needs acknowledgement before defence
- Never lie, minimise, or deflect in crisis communications
- Crisis response: Acknowledge → Clarify facts → Commit to action → Follow up
- Press releases should be newsworthy, not self-promotional puff pieces
- Brand voice: professional, confident, human — never corporate-speak

Urgency levels: low (positive/neutral), medium (minor negative), high (significant negative), crisis (viral, legal risk, or major reputational threat)"""


class LumaEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def analyse_mention(self, mention, instance=None) -> dict:
        prompt = f"""Analyse this brand mention for sentiment, urgency, and required action.

Source: {mention.source}
Title: {mention.title}
Snippet: {mention.snippet}
URL: {mention.url}

Return JSON:
{{
  "sentiment": "positive|neutral|negative",
  "urgency": "low|medium|high|crisis",
  "ai_summary": "2-sentence analysis of this mention and its potential impact",
  "response_required": boolean,
  "response_tone": "appreciative|informative|defensive|apologetic|proactive",
  "recommended_action": "specific action to take",
  "crisis_indicators": ["list of crisis signals if any"]
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"sentiment": "neutral", "urgency": "low", "ai_summary": raw, "response_required": False}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"analyse_mention for mention {mention.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if res.get("urgency") == "crisis":
                raise PermissionRequired(
                    context=f"CRISIS DETECTED! Mention from {mention.source} flagged as crisis. Summary: {res.get('ai_summary')}",
                    option_a="Approve generation of immediate holding statement & PR alert",
                    option_b="Deny (Handle internally)"
                )
        return res

    def draft_response(self, mention, instance=None) -> str:
        prompt = f"""Draft a public-facing response to this brand mention.

Source: {mention.source}
Title: {mention.title}
Snippet: {mention.snippet}
Sentiment: {mention.sentiment}
Urgency: {mention.urgency}

Write a response that:
- Acknowledges the mention appropriately for the sentiment
- Is on-brand (professional, human, confident)
- Includes a clear, constructive next step
- Is appropriate for public posting on {mention.source}

Write ONLY the response text, no preamble."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"draft_response for mention {mention.pk}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def generate_press_release(self, release, instance=None) -> str:
        prompt = f"""Write a professional press release.

Headline: {release.headline}
Boilerplate: {release.boilerplate}

Structure:
- Dateline + headline
- Opening paragraph (who, what, when, where, why — the news)
- Quote from company spokesperson
- Supporting details and context
- Another quote if relevant
- Boilerplate (use provided)
- Contact: [Media Contact Placeholder]

Write a complete, wire-ready press release."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"generate_press_release for {release.headline}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def crisis_playbook(self, crisis_description: str, instance=None) -> dict:
        prompt = f"""Generate a crisis communication playbook for this situation.

Crisis: {crisis_description}

Return JSON:
{{
  "immediate_actions": ["first 1 hour actions"],
  "holding_statement": "what to say publicly right now while investigating",
  "key_messages": ["3-5 core messages to stay on"],
  "what_not_to_say": ["things to avoid"],
  "media_response": "full media statement draft",
  "internal_comms": "what to tell employees",
  "monitoring_plan": "how to track escalation",
  "resolution_timeline": "expected resolution path"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"immediate_actions": [], "holding_statement": raw, "key_messages": [], "what_not_to_say": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="crisis_playbook generated",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
