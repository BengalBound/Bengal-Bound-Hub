import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Serea Content, BengalBound's AI Content Strategist.

Your role is to build content strategies that grow audiences, establish thought leadership, and drive measurable business outcomes. You plan strategically and execute creatively.

Capabilities:
- Create content pieces across blog, email, social, and ad formats
- Build comprehensive content campaigns with clear objectives and KPIs
- Develop content calendars aligned to business goals
- Audit existing content for gaps, quality, and opportunity
- Write in diverse brand voices from corporate to conversational
- Optimise content for distribution and amplification

Principles:
- Content strategy starts with audience: who reads this, why do they care, what do they do next?
- Every piece needs a distribution plan — great content no one sees is wasted effort
- Repurpose aggressively: a good idea works across 5+ formats
- Measure what matters: traffic, leads, and revenue — not just views
- Brand voice is everything: inconsistent voice destroys brand trust

Content types: blog_post, email, social, ad_copy

[STRICT SYSTEM RULES]
1. OUTPUT: Return ONLY raw JSON if requested. NO markdown (```json), NO filler.
2. REASONING: Think step-by-step internally, output final answer only.
3. DOMAIN: Decline out-of-scope tasks. Zero hallucinations.
4. TONE: Professional human employee. Never identify as AI/bot.

"""


class ContentStrategistEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def generate_piece(self, piece, instance=None) -> str:
        type_guides = {
            "blog_post": "Long-form, 800-1500 words, H2/H3 structure, SEO-optimised, practical and authoritative",
            "email": "Subject + preview + body, scannable, single CTA, conversational tone",
            "social": "Hook (grabs attention) + value + CTA. Concise and shareable.",
            "ad_copy": "Headline (≤30 chars) + body (≤90 chars) + CTA button text. Benefits over features.",
        }
        guide = type_guides.get(piece.content_type, "Clear, engaging, on-brand content")

        prompt = f"""Write this content piece.

Title: {piece.title}
Type: {piece.content_type}
Brief/Instructions: {piece.prompt}

Format guidance: {guide}

Write complete, publish-ready content."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"generate_piece {piece.pk}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def campaign_strategy(self, campaign, instance=None) -> dict:
        prompt = f"""Build a content campaign strategy.

Campaign: {campaign.name}
Goal: {campaign.goal or 'Not specified'}

Return JSON:
{{
  "strategy_overview": "2-paragraph campaign strategy",
  "content_pillars": ["3-5 core themes/topics"],
  "content_mix": {{"blog_post": integer, "email": integer, "social": integer, "ad_copy": integer}},
  "kpis": ["measurable success metrics"],
  "distribution_plan": "how to distribute and amplify",
  "content_calendar_suggestion": [
    {{"week": 1, "title": "content title", "type": "blog_post|email|social|ad_copy", "goal": "what this achieves"}}
  ]
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"strategy_overview": raw, "content_pillars": [], "kpis": [], "content_mix": {}}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"campaign_strategy {campaign.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            raise PermissionRequired(
                context=f"New Content Campaign Strategy drafted for: {campaign.name}. Requires approval before generating pieces.",
                option_a="Approve strategy and begin generating content",
                option_b="Deny and request strategic revision"
            )
        return res

    def content_audit(self, pieces: list, instance=None) -> dict:
        pieces_summary = "\n".join(
            f"- [{p.content_type}] {p.title} (status: {p.status})"
            for p in pieces[:20]
        )
        prompt = f"""Audit this content inventory for gaps and quality.

Content Inventory:
{pieces_summary}

Return JSON:
{{
  "content_gaps": ["topics or types missing"],
  "underperforming": ["pieces to retire or rewrite"],
  "quick_wins": ["easy improvements to make this week"],
  "strategic_recommendation": "overall content strategy recommendation"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"content_gaps": [], "underperforming": [], "quick_wins": [], "strategic_recommendation": raw}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="content_audit",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
