import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Sage, BengalBound's AI Legal Reviewer.

Your role is to make legal documents understandable, identify risks before they become liabilities, and help businesses negotiate from a position of knowledge. You are not a lawyer, but you are a rigorous legal analyst.

Capabilities:
- Review contracts, NDAs, employment agreements, and vendor contracts
- Identify high-risk clauses with plain-English explanations
- Score overall document risk from 0-100
- Generate negotiation suggestions for unfavourable clauses
- Flag missing standard protections (limitation of liability, termination rights, etc.)
- Compare clauses against standard market terms

Principles:
- Always recommend legal counsel for high-risk or complex documents
- Risk ratings: safe (standard terms), caution (negotiate), risky (significant exposure), critical (do not sign without counsel)
- Plain English is non-negotiable — if you can't explain it simply, flag it for human review
- Missing clauses can be as dangerous as bad ones — identify what's absent
- Flag jurisdiction-specific risks (Bangladesh law vs. international contracts)
- Never provide legal advice — provide legal analysis with a recommendation to consult counsel

Document types: NDA, contract, employment, vendor, compliance, other

[STRICT SYSTEM RULES]
1. OUTPUT: Return ONLY raw JSON if requested. NO markdown (```json), NO filler.
2. REASONING: Think step-by-step internally, output final answer only.
3. DOMAIN: Decline out-of-scope tasks. Zero hallucinations.
4. TONE: Professional human employee. Never identify as AI/bot.

"""


class SageEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def review_document(self, document, instance=None) -> dict:
        text_preview = document.raw_text[:4000] if document.raw_text else "Document text not provided"
        prompt = f"""Review this {document.document_type} document for legal risks.

Document: {document.name}
Type: {document.document_type}
Text:
{text_preview}

Return JSON:
{{
  "overall_risk": integer 0-100,
  "risk_label": "low|medium|high|critical",
  "executive_summary": "3-paragraph plain-English document summary",
  "critical_issues": ["issues requiring immediate attention"],
  "missing_protections": ["standard clauses that are absent"],
  "clauses": [
    {{
      "clause_title": "name of clause",
      "original_text": "relevant extract",
      "plain_english": "what this means in plain English",
      "risk_level": "safe|caution|risky|critical",
      "risk_score": integer 0-100,
      "negotiation_suggestion": "specific negotiation recommendation"
    }}
  ],
  "counsel_required": boolean
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"overall_risk": 50, "risk_label": "medium", "executive_summary": raw, "clauses": [], "critical_issues": [], "missing_protections": [], "counsel_required": True}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"review_document for {document.name}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if res.get("risk_label") == "critical" or res.get("counsel_required"):
                raise PermissionRequired(
                    context=f"CRITICAL LEGAL RISK in {document.name}. AI recommends external legal counsel.",
                    option_a="Approve escalating to external legal counsel",
                    option_b="Deny (Handle internally)"
                )
        return res

    def explain_clause(self, clause, instance=None) -> dict:
        prompt = f"""Explain this legal clause in plain English and provide negotiation advice.

Clause: {clause.clause_title or 'Untitled clause'}
Text:
{clause.original_text}

Return JSON:
{{
  "plain_english": "clear, jargon-free explanation of what this clause means",
  "risk_level": "safe|caution|risky|critical",
  "risk_score": integer 0-100,
  "key_risks": ["specific risks this clause creates"],
  "negotiation_suggestion": "specific language to negotiate",
  "market_standard": "is this clause standard, aggressive, or lenient?"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"plain_english": raw, "risk_level": "caution", "risk_score": 50, "negotiation_suggestion": "", "key_risks": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"explain_clause {clause.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def contract_comparison(self, clause_text: str, standard_term: str, instance=None) -> dict:
        prompt = f"""Compare this contract clause to the market standard.

Proposed Clause:
{clause_text[:1000]}

Market Standard:
{standard_term[:500]}

Return JSON:
{{
  "more_favourable": boolean (is the proposed clause more favourable than standard?),
  "key_differences": ["list of material differences"],
  "negotiate_towards": "suggested language closer to market standard",
  "walkaway_point": "at what point should you refuse to sign?"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"more_favourable": False, "key_differences": [], "negotiate_towards": raw, "walkaway_point": ""}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="contract_comparison",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
