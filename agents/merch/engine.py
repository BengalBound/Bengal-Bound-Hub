import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Merch, BengalBound's AI eCommerce Manager.

Your role is to maximise GMV and conversion rates across every sales channel. You optimise listings, price strategically, and keep inventory healthy.

Capabilities:
- Generate compelling, SEO-optimised product descriptions
- Recommend pricing based on demand, competition, and margin
- Detect low-stock risks and trigger reorder alerts
- Analyse 30-day sales trends and surface opportunities
- A/B test listing copy and surfaces improvement recommendations
- Manage multi-platform inventory and listing sync

Principles:
- Product descriptions should sell benefits, not just features
- Platform-specific: Daraz SEO differs from Shopify SEO — know each platform's algorithm
- Price positioning: compete on value, not just price — margin matters
- Low stock = lost sales = customer churn — monitor proactively
- Fast-movers deserve more inventory; slow-movers deserve a price cut or delisting
- Always include a CTA in product descriptions

Platforms: shopify, woocommerce, daraz, facebook, custom

[STRICT SYSTEM RULES]
1. OUTPUT: Return ONLY raw JSON if requested. NO markdown (```json), NO filler.
2. REASONING: Think step-by-step internally, output final answer only.
3. DOMAIN: Decline out-of-scope tasks. Zero hallucinations.
4. TONE: Professional human employee. Never identify as AI/bot.

"""


class MerchEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def optimise_listing(self, product, instance=None) -> dict:
        platform_tips = {
            "shopify": "SEO-optimised, storytelling style, 150-300 words",
            "woocommerce": "Feature-benefit format, include specs, SEO keyword rich",
            "daraz": "Keyword-heavy title, bullet points, local language if appropriate",
            "facebook": "Conversational, social proof focus, emoji-friendly",
            "custom": "Professional, clear, benefit-led",
        }
        platform = product.store.platform if product.store else "custom"
        tip = platform_tips.get(platform, "Clear, compelling product description")

        prompt = f"""Optimise this product listing for {platform}.

Product: {product.title}
Current SKU: {product.sku}
Current Price: {product.price} {product.store.currency if product.store else 'BDT'}
Units Sold (30d): {product.units_sold_30d}
Stock: {product.stock_quantity}

Platform guideline: {tip}

Return JSON:
{{
  "ai_description": "optimised product description",
  "title_suggestion": "improved product title if applicable",
  "ai_price": "recommended price (decimal)",
  "pricing_rationale": "why this price",
  "tags": ["relevant search tags"],
  "improvement_notes": ["what was changed and why"]
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"ai_description": raw, "ai_price": float(product.price), "pricing_rationale": "", "tags": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"optimise_listing for {product.sku}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            # If changing price, ask permission
            if res.get("ai_price") and float(res["ai_price"]) != float(product.price):
                raise PermissionRequired(
                    context=f"Merch wants to change price for {product.title} from {product.price} to {res['ai_price']}. Reason: {res.get('pricing_rationale')}",
                    option_a=f"Approve price change to {res['ai_price']}",
                    option_b="Deny (Keep current price)"
                )
        return res

    def sales_analysis(self, store, products: list, instance=None) -> str:
        product_summary = "\n".join(
            f"- {p.title}: {p.units_sold_30d} sold, stock: {p.stock_quantity}, price: {p.price}"
            for p in products[:20]
        )
        prompt = f"""Analyse 30-day sales performance for {store.store_name} ({store.platform}).

Products:
{product_summary}

Provide:
1. Top performers — what's working and why
2. Underperformers — what to do (price cut, new description, deactivate)
3. Inventory risks — what will stock out soon
4. Recommended actions for this week"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"sales_analysis for {store.store_name}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def reorder_recommendation(self, product, instance=None) -> dict:
        prompt = f"""Generate a reorder recommendation for this product.

Product: {product.title}
Current Stock: {product.stock_quantity}
Reorder Threshold: {product.reorder_threshold}
Units Sold (30d): {product.units_sold_30d}

Return JSON:
{{
  "should_reorder": boolean,
  "recommended_quantity": integer,
  "urgency": "low|medium|high|critical",
  "days_of_stock_remaining": integer,
  "reasoning": "brief explanation"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"should_reorder": product.stock_quantity < product.reorder_threshold, "recommended_quantity": 100, "urgency": "medium", "reasoning": raw}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"reorder_recommendation for {product.sku}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if res.get("should_reorder") and res.get("urgency") in ["high", "critical"]:
                raise PermissionRequired(
                    context=f"Critical low stock for {product.title}. Recommended reorder: {res.get('recommended_quantity')} units. Reason: {res.get('reasoning')}",
                    option_a=f"Approve creating purchase order for {res.get('recommended_quantity')} units",
                    option_b="Deny"
                )
        return res
