import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Pulse, BengalBound's AI Market Research Analyst.

Your role is to keep businesses ahead of market shifts. You synthesise intelligence from multiple signals, spot trends before they peak, and turn research into strategic advantage.

Capabilities:
- Conduct comprehensive market research and competitive analysis
- Identify growth opportunities and emerging threats
- Analyse industry trends and their business implications
- Monitor competitor movements and signal strategic responses
- Generate executive-ready research reports
- Map market opportunities against business strengths

Principles:
- Research should be actionable, not academic
- Distinguish between correlation and causation when identifying trends
- Rate every finding by confidence level (high/medium/low)
- Competitor intelligence: what they're doing > what they're saying
- Opportunities should be scored by market size × ease of capture
- Every report should end with a clear strategic recommendation

Report structure: Executive Summary → Key Findings → Opportunities → Threats → Recommendations

[STRICT SYSTEM RULES]
1. OUTPUT: Return ONLY raw JSON if requested. NO markdown (```json), NO filler.
2. REASONING: Think step-by-step internally, output final answer only.
3. DOMAIN: Decline out-of-scope tasks. Zero hallucinations.
4. TONE: Professional human employee. Never identify as AI/bot.

"""


class PulseEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def generate_report(self, config, report, instance=None) -> dict:
        keywords = ", ".join(config.keywords[:10]) if config.keywords else "Not specified"
        competitors = ", ".join(config.competitors[:5]) if config.competitors else "Not specified"
        markets = ", ".join(config.target_markets[:5]) if config.target_markets else "Not specified"

        prompt = f"""Generate a comprehensive market research report.

Industry: {config.industry}
Tracking Keywords: {keywords}
Key Competitors: {competitors}
Target Markets: {markets}
Report Period: {report.period}

Return JSON:
{{
  "narrative": "3-5 paragraph market narrative with key developments",
  "key_findings": [
    {{"finding": "...", "confidence": "high|medium|low", "source_type": "...", "business_relevance": "high|medium|low"}}
  ],
  "opportunities": [
    {{"opportunity": "...", "market_size": "...", "ease_of_capture": "high|medium|low", "action": "..."}}
  ],
  "threats": [
    {{"threat": "...", "probability": "high|medium|low", "impact": "high|medium|low", "mitigation": "..."}}
  ],
  "recommendations": [
    {{"recommendation": "...", "priority": "immediate|short_term|long_term", "expected_outcome": "..."}}
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
            res = {"narrative": raw, "key_findings": [], "opportunities": [], "threats": [], "recommendations": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"generate_report {report.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            high_threats = [t.get("threat") for t in res.get("threats", []) if t.get("probability") == "high" and t.get("impact") == "high"]
            if high_threats:
                raise PermissionRequired(
                    context=f"Critical market threats identified: {', '.join(high_threats[:2])}",
                    option_a="Acknowledge and trigger strategy review",
                    option_b="Dismiss as false alarm"
                )
        return res

    def trend_analysis(self, industry: str, keywords: list, instance=None) -> str:
        keywords_text = ", ".join(keywords[:10])
        prompt = f"""Analyse current trends in the {industry} industry.

Tracking keywords: {keywords_text}

Provide:
1. Top 3 emerging trends (with evidence and implications)
2. Declining trends to exit
3. Technology shifts affecting this industry
4. Consumer behaviour changes
5. Regulatory developments to watch"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="trend_analysis",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def competitor_analysis(self, competitors: list, own_company: str, instance=None) -> dict:
        comp_text = "\n".join(f"- {c}" for c in competitors[:5])
        prompt = f"""Analyse the competitive landscape for {own_company}.

Key Competitors:
{comp_text}

Return JSON:
{{
  "competitive_position": "leader|challenger|follower|niche",
  "differentiation_opportunities": ["gaps in competitor offerings"],
  "competitive_threats": ["what competitors could do to hurt us"],
  "positioning_recommendation": "how to position against the competition",
  "battle_cards": [
    {{"competitor": "name", "their_strength": "...", "our_counter": "..."}}
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
            res = {"competitive_position": "challenger", "differentiation_opportunities": [], "competitive_threats": [], "battle_cards": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="competitor_analysis",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
