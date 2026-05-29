import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Flux, BengalBound's AI Supply Chain Manager.

Your role is to keep supply chains resilient, cost-efficient, and disruption-proof. You proactively identify risks and act before stock-outs or supplier failures happen.

Capabilities:
- Score supplier performance using on-time rate, lead times, and quality data
- Generate purchase order recommendations with quantity and timing
- Detect stock risks before they become shortages
- Evaluate and compare vendor bids and quotes
- Identify single-point-of-failure supplier dependencies
- Build contingency sourcing plans

Principles:
- Never let stock drop below safety threshold without a PO in progress
- Diversify critical item suppliers — single sourcing is a risk flag
- Total cost of ownership matters, not just unit price
- Lead time accuracy is as important as price
- Always have a Plan B supplier for critical components
- Flag overdue POs and slow suppliers before they cause disruption

Rating scale: excellent (≥95% on-time, ≤3 avg lead days), good, average, poor

[STRICT SYSTEM RULES]
1. OUTPUT: Return ONLY raw JSON if requested. NO markdown (```json), NO filler.
2. REASONING: Think step-by-step internally, output final answer only.
3. DOMAIN: Decline out-of-scope tasks. Zero hallucinations.
4. TONE: Professional human employee. Never identify as AI/bot.

"""


class FluxEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def assess_supplier(self, supplier, instance=None) -> dict:
        prompt = f"""Assess this supplier's performance and provide a rating.

Supplier: {supplier.name}
Country: {supplier.country or 'Unknown'}
On-Time Delivery Rate: {supplier.on_time_rate}%
Average Lead Time: {supplier.avg_lead_days} days
Current Rating: {supplier.rating}

Return JSON:
{{
  "rating": "excellent|good|average|poor",
  "ai_summary": "2-paragraph supplier assessment",
  "risks": ["list of risks"],
  "strengths": ["list of strengths"],
  "recommendations": ["specific improvement recommendations"],
  "should_diversify": boolean
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"rating": supplier.rating, "ai_summary": raw, "risks": [], "strengths": [], "recommendations": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"assess_supplier {supplier.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if res.get("rating") == "poor":
                raise PermissionRequired(
                    context=f"Supplier {supplier.name} assessed as POOR. Consider replacing.",
                    option_a="Acknowledge and start vendor search",
                    option_b="Ignore warning"
                )
        return res

    def po_recommendation(self, order, instance=None) -> str:
        items_text = json.dumps(order.items, indent=2) if order.items else "No items listed"
        prompt = f"""Provide a sourcing recommendation for this purchase order.

PO Number: {order.po_number}
Supplier: {order.supplier.name} (rating: {order.supplier.rating})
Expected Delivery: {order.expected_date}
Total Value: BDT {order.total_value:,.2f}
Items:
{items_text}

Provide:
1. Assessment of this supplier for these items
2. Whether to proceed, negotiate, or seek alternatives
3. Specific negotiation points if applicable
4. Alternative supplier suggestions if rating is below 'good'"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"po_recommendation {order.pk}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def stock_risk_analysis(self, low_stock_items: list, instance=None) -> dict:
        items_text = "\n".join(
            f"- {item.get('name', 'Unknown')}: {item.get('qty', 0)} units (threshold: {item.get('threshold', 0)})"
            for item in low_stock_items[:20]
        )
        prompt = f"""Analyse stock risk for these low-stock items.

Low Stock Items:
{items_text}

Return JSON:
{{
  "critical_items": ["items needing immediate PO"],
  "watch_items": ["items to monitor"],
  "overall_risk": "low|medium|high|critical",
  "recommended_actions": ["specific actions with timelines"],
  "estimated_stockout_risk": "description of business impact if not addressed"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"critical_items": [], "watch_items": [], "overall_risk": "medium", "recommended_actions": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="stock_risk_analysis",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if res.get("overall_risk") == "critical":
                raise PermissionRequired(
                    context=f"CRITICAL stock risk identified! Critical items: {', '.join(res.get('critical_items', []))}",
                    option_a="Approve emergency POs",
                    option_b="Deny and investigate"
                )
        return res
