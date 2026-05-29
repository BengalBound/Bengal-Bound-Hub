import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Oracle, BengalBound's AI SEO Specialist.

Your role is to drive sustainable organic traffic growth. You audit with precision, fix issues that actually move rankings, and never chase algorithm shortcuts.

Capabilities:
- Audit websites for technical SEO, on-page, and off-page issues
- Generate fix implementations (not just recommendations)
- Research high-value keywords with ranking opportunity
- Optimise meta titles, descriptions, and heading structures
- Fix schema markup, canonical tags, and internal linking
- Monitor and report ranking progress

Principles:
- Prioritise fixes by ranking impact: critical (page not indexed) > high (missing meta) > medium (slow page) > low (missing alt)
- Technical SEO first, then on-page, then off-page
- Every fix must include: what to change, where, and expected impact
- Keyword targeting: search intent matters more than volume
- Don't chase exact-match keywords — write for humans, optimise for search
- Core Web Vitals are ranking signals — performance fixes are SEO fixes

Issue severity: critical (page not visible/indexed), warning (significant ranking drag), info (minor improvement)

[STRICT SYSTEM RULES]
1. OUTPUT: Return ONLY raw JSON if requested. NO markdown (```json), NO filler.
2. REASONING: Think step-by-step internally, output final answer only.
3. DOMAIN: Decline out-of-scope tasks. Zero hallucinations.
4. TONE: Professional human employee. Never identify as AI/bot.

"""


class OracleEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def audit_website(self, website, instance=None) -> list:
        prompt = f"""Run an SEO audit assessment for this website.

Domain: {website.domain}
CMS: {website.cms or 'Unknown'}
Last crawled: {website.last_crawled or 'Never'}

Generate a comprehensive SEO audit identifying issues across:
1. Technical (crawlability, indexation, site speed, mobile)
2. On-page (titles, metas, headings, content)
3. Off-page (backlinks, brand signals)
4. Core Web Vitals (LCP, FID, CLS)

Return a JSON array of issues:
{{
  "issue_type": "missing_meta|broken_link|duplicate_content|slow_page|missing_schema|mobile_issue|missing_alt",
  "severity": "critical|warning|info",
  "page_url": "example page URL pattern",
  "description": "specific description of the issue",
  "fix_suggestion": "exact implementation steps to fix this",
  "estimated_impact": "low|medium|high"
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
                action=f"audit_website for {website.domain}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            has_critical = any(r.get("severity") == "critical" for r in res)
            if has_critical:
                raise PermissionRequired(
                    context=f"CRITICAL SEO issue found on {website.domain}. Immediate fix recommended.",
                    option_a="Approve creating urgent dev ticket",
                    option_b="Deny (Handle internally)"
                )
        return res

    def generate_fix(self, issue, instance=None) -> str:
        prompt = f"""Generate a complete, implementable fix for this SEO issue.

Issue Type: {issue.issue_type}
Severity: {issue.severity}
Page: {issue.page_url}
Description: {issue.description}

Provide:
1. Exact implementation (code/HTML if applicable)
2. Where to make the change (which file/template/setting)
3. How to verify the fix worked
4. Expected ranking impact timeline"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"generate_fix for issue {issue.pk}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def keyword_research(self, niche: str, current_domain: str, instance=None) -> dict:
        prompt = f"""Conduct keyword research for this business niche.

Niche: {niche}
Domain: {current_domain}

Return JSON:
{{
  "primary_keywords": [
    {{"keyword": "...", "search_intent": "informational|navigational|transactional|commercial", "difficulty": "low|medium|high", "opportunity_score": integer 0-100}}
  ],
  "long_tail_opportunities": ["list of long-tail keyword phrases"],
  "content_gaps": ["topics competitors cover but this site likely doesn't"],
  "quick_wins": ["keywords where this domain could rank quickly"],
  "strategy_summary": "2-paragraph keyword strategy recommendation"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"primary_keywords": [], "long_tail_opportunities": [], "content_gaps": [], "quick_wins": [], "strategy_summary": raw}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"keyword_research for {niche}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def meta_optimisation(self, page_url: str, page_title: str, page_content: str, target_keyword: str, instance=None) -> dict:
        prompt = f"""Optimise meta tags for this page.

URL: {page_url}
Current Title: {page_title}
Target Keyword: {target_keyword}
Content Preview: {page_content[:500]}

Return JSON:
{{
  "meta_title": "optimised title (50-60 chars, keyword near front)",
  "meta_description": "optimised description (145-160 chars, includes keyword, has CTA)",
  "h1_suggestion": "primary heading",
  "schema_type": "recommended schema markup type"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"meta_title": page_title, "meta_description": page_content[:155], "h1_suggestion": page_title}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"meta_optimisation for {page_url}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
