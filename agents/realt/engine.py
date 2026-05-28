import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Realt, BengalBound's AI Real Estate Assistant.

Your role is to maximise property transactions and lead conversion. You write listings that attract buyers, qualify leads precisely, and match properties to buyers efficiently.

Capabilities:
- Generate compelling, SEO-optimised property listing descriptions
- Qualify buyer and seller leads by budget, intent, and timeline
- Match properties to leads based on criteria and budget
- Analyse market data and provide pricing recommendations
- Draft offer letters, viewing confirmations, and follow-up communications
- Generate neighbourhood and comparative market analyses

Principles:
- Listings should sell a lifestyle, not just a property
- Lead qualification: budget fit (40%) + intent seriousness (35%) + timeline (25%)
- Never overstate property features — accurate representation prevents disputes
- High-intent leads (buying/renting within 90 days) get priority follow-up
- AI scores are advisory — the human agent makes the final qualification call
- Always check: does this lead's budget match available inventory?

Property types: apartment, house, commercial, land, office
Listing types: sale, rent"""


class RealtEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def generate_listing(self, property_obj, instance=None) -> str:
        bedrooms_text = f"{property_obj.bedrooms} bedrooms" if property_obj.bedrooms else "studio/open plan"
        prompt = f"""Write a compelling property listing description.

Title: {property_obj.title}
Type: {property_obj.property_type} — {property_obj.listing_type}
Price: BDT {property_obj.price:,.0f}
Area: {property_obj.area_sqft:,} sq ft
Bedrooms: {bedrooms_text}
Location: {property_obj.location}
Raw Description: {property_obj.description or 'No description provided'}

Write an engaging, accurate listing that:
1. Opens with the strongest feature or lifestyle benefit
2. Highlights key selling points naturally
3. Describes the location and its advantages
4. Ends with a clear call to action
Target 150-250 words. No exaggeration."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"generate_listing {property_obj.pk}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def qualify_lead(self, lead, instance=None) -> dict:
        areas = ", ".join(lead.preferred_areas) if lead.preferred_areas else "Flexible"
        prompt = f"""Qualify this real estate lead.

Name: {lead.name}
Intent: {lead.intent} (buy/rent)
Budget Max: BDT {lead.budget_max:,.0f} if lead.budget_max else 'Not specified'
Preferred Areas: {areas}
Bedrooms Needed: {lead.bedrooms_needed or 'Flexible'}
Status: {lead.status}

Return JSON:
{{
  "ai_score": integer 0-100,
  "qualification": "hot|warm|cold|unqualified",
  "ai_notes": "2-paragraph qualification assessment",
  "timeline_estimate": "estimated purchase/rental timeline",
  "next_action": "specific next step for the agent",
  "property_matches_needed": "what inventory to show this lead",
  "budget_reality_check": "is the budget realistic for their requirements?"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"ai_score": 50, "qualification": "warm", "ai_notes": raw, "next_action": "Follow up with lead"}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"qualify_lead {lead.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if res.get("qualification") == "unqualified":
                raise PermissionRequired(
                    context=f"Lead {lead.name} marked UNQUALIFIED. Rationale: {res.get('ai_notes')}",
                    option_a="Approve and discard lead",
                    option_b="Deny and assign to agent for follow-up"
                )
        return res

    def property_match(self, lead, properties: list, instance=None) -> list:
        props_text = "\n".join(
            f"- {p.title}: {p.property_type}, {p.area_sqft} sqft, BDT {p.price:,.0f}, {p.location}, {p.bedrooms or 'N/A'} beds"
            for p in properties[:20]
        )
        budget_text = f"BDT {lead.budget_max:,.0f}" if lead.budget_max else "Not specified"

        prompt = f"""Match this lead to the best available properties.

Lead: {lead.name}
Intent: {lead.intent}
Budget: {budget_text}
Areas: {', '.join(lead.preferred_areas) if lead.preferred_areas else 'Flexible'}
Bedrooms: {lead.bedrooms_needed or 'Flexible'}

Available Properties:
{props_text}

Return a JSON array of the top 3 matches:
{{
  "property_title": "...",
  "match_score": integer 0-100,
  "match_rationale": "why this property fits",
  "viewing_pitch": "how to pitch this viewing to the lead"
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
                action=f"property_match for {lead.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
