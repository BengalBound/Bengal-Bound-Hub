import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Clarity, BengalBound's AI Feedback Analyst.

Your role is to turn raw customer and employee feedback into actionable intelligence. You find patterns humans miss and surface insights that drive decisions.

Capabilities:
- Extract recurring themes from survey responses and reviews
- Perform sentiment analysis at theme and individual response level
- Calculate priority scores based on frequency + severity + business impact
- Generate executive insight reports
- Identify emerging issues before they become crises
- Recommend specific product, process, or policy changes

Principles:
- Patterns matter more than individual responses
- Quantify everything possible (frequency, severity, impact score)
- Distinguish noise from signal — not every complaint is a theme
- Always link insights to actionable recommendations
- Surface positive themes too, not just pain points
- Group similar feedback even if worded differently

Analysis types: NPS, CSAT, feature requests, exit surveys, employee engagement, post-session"""


class ClarityEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def extract_themes(self, responses: list, survey_name: str, instance=None) -> list:
        response_text = "\n".join(f"- {r}" for r in responses[:100])
        prompt = f"""Analyse these survey responses from "{survey_name}" and extract key themes.

Responses:
{response_text}

Return a JSON array of theme objects:
{{
  "theme": "theme label",
  "theme_type": "pain_point|feature_request|praise|confusion",
  "mention_count": integer,
  "priority_score": integer 0-100,
  "example_quotes": ["quote1", "quote2"],
  "ai_analysis": "2-3 sentence analysis of this theme",
  "recommendation": "specific actionable recommendation"
}}"""

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
                action="extract_themes",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def analyse_theme(self, theme, instance=None) -> dict:
        prompt = f"""Deeply analyse this feedback theme.

Theme: {theme.theme}
Type: {theme.theme_type}
Mentions: {theme.mention_count}
Example quotes:
{json.dumps(theme.example_quotes, indent=2)}

Provide:
1. Root cause analysis
2. Business impact assessment (revenue, retention, NPS)
3. Urgency level (critical/high/medium/low)
4. Three specific, actionable recommendations with owners (product/engineering/CS/marketing)
5. How to measure improvement

Return as JSON: {{"analysis": "...", "root_cause": "...", "business_impact": "...", "urgency": "...", "recommendations": [], "success_metrics": []}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"analysis": raw, "urgency": "medium", "recommendations": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"analyse_theme for {theme.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if res.get("urgency") == "critical":
                raise PermissionRequired(
                    context=f"CRITICAL feedback theme detected: {theme.theme}. Analysis: {res.get('analysis')}",
                    option_a="Acknowledge and assign owners",
                    option_b="Deny priority (mark as false alarm)"
                )
        return res

    def sentiment_score(self, text: str, instance=None) -> dict:
        prompt = f"""Score the sentiment of this feedback.

Text: {text[:1000]}

Return JSON: {{"sentiment": "positive|neutral|negative", "score": float -1 to 1, "emotions": ["list of detected emotions"], "intensity": "low|medium|high"}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"sentiment": "neutral", "score": 0.0, "emotions": [], "intensity": "low"}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="sentiment_score",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def weekly_insight_report(self, themes: list, period: str, instance=None) -> str:
        theme_summary = "\n".join(
            f"- [{t.theme_type}] {t.theme} (score: {t.priority_score}, mentions: {t.mention_count})"
            for t in themes[:15]
        )
        prompt = f"""Generate a weekly feedback insight report for the period: {period}

Top Themes:
{theme_summary}

Write a 3-section report:
1. Executive Summary (key findings in 2 sentences)
2. Top 5 Priorities with recommended owners and actions
3. Emerging trends to watch next week"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="weekly_insight_report",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
