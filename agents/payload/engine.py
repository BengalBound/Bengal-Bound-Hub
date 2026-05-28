import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Payload, BengalBound's AI Procurement Manager.

Your role is to ensure the organisation gets the best value from every purchase. You source strategically, evaluate objectively, and protect the business from supplier risk.

Capabilities:
- Evaluate RFQ responses and rank vendors by value (not just price)
- Score vendor performance across quality, cost, delivery, and service
- Identify procurement risks (single sourcing, overreliance, poor terms)
- Generate purchase recommendations with full justification
- Draft RFQ documents and vendor scorecards
- Negotiate guidance and benchmark pricing

Principles:
- Total cost of ownership, not lowest price — include delivery, quality risk, and support
- Vendor diversification: no single vendor should represent >40% of category spend
- Evaluate: quality (30%), price (30%), delivery reliability (25%), support (15%)
- Payment terms matter: longer terms improve cash flow — negotiate these aggressively
- Blacklist triggers: 2+ SLA breaches, quality failures, or compliance violations
- Document every procurement decision with a clear business justification"""


class PayloadEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def evaluate_rfq(self, rfq, vendors: list, instance=None) -> dict:
        vendor_context = "\n".join(
            f"- {v.name} (score: {v.performance_score or 'N/A'}, terms: {v.payment_terms or 'Unknown'}, country: {v.country or 'Unknown'})"
            for v in vendors
        )
        requirements_text = json.dumps(rfq.requirements, indent=2) if rfq.requirements else "Not specified"

        prompt = f"""Evaluate this RFQ and recommend the best vendor.

RFQ: {rfq.title}
Description: {rfq.description}
Requirements:
{requirements_text}
Deadline: {rfq.deadline}

Available Vendors:
{vendor_context}

Return JSON:
{{
  "recommended_vendor": "vendor name",
  "recommendation_rationale": "specific justification",
  "vendor_ranking": [
    {{"rank": 1, "vendor": "name", "score": integer 0-100, "strengths": [], "weaknesses": []}}
  ],
  "negotiation_points": ["specific items to negotiate"],
  "risk_flags": ["procurement risks to address"],
  "ai_recommendation": "2-paragraph executive procurement recommendation"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"recommended_vendor": "Requires human review", "ai_recommendation": raw, "vendor_ranking": [], "negotiation_points": [], "risk_flags": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"evaluate_rfq {rfq.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if res.get("risk_flags") and len(res.get("risk_flags")) > 0:
                raise PermissionRequired(
                    context=f"Procurement risk flags identified in RFQ {rfq.title}: {', '.join(res.get('risk_flags', []))}",
                    option_a="Acknowledge risks and proceed with vendor",
                    option_b="Deny and issue new RFQ"
                )
        return res

    def assess_vendor(self, vendor, instance=None) -> dict:
        prompt = f"""Assess this vendor's overall performance and suitability.

Vendor: {vendor.name}
Category: {vendor.category}
Country: {vendor.country or 'Unknown'}
Payment Terms: {vendor.payment_terms or 'Unknown'}
Performance Score: {vendor.performance_score or 'Not scored'}/100
Status: {vendor.status}

Return JSON:
{{
  "overall_score": integer 0-100,
  "status_recommendation": "active|on_hold|blacklisted",
  "strengths": ["list of strengths"],
  "risks": ["list of risks"],
  "recommended_actions": ["specific actions"],
  "tier": "strategic|preferred|approved|conditional"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"overall_score": 50, "status_recommendation": "active", "strengths": [], "risks": [], "recommended_actions": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"assess_vendor {vendor.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def draft_rfq(self, title: str, description: str, budget_range: str, deadline: str, instance=None) -> str:
        prompt = f"""Draft a professional Request for Quotation (RFQ) document.

Title: {title}
Description: {description}
Budget Range: {budget_range}
Response Deadline: {deadline}

Include:
1. RFQ introduction and overview
2. Scope of requirements (detailed)
3. Vendor qualification criteria
4. Evaluation criteria with weightings
5. Submission instructions
6. Terms and conditions summary"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="draft_rfq",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
