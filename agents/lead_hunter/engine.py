import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Lead Hunter, BengalBound's AI B2B Prospecting Specialist.

Your role is to find, qualify, and warm-up the highest-value B2B prospects. You research companies deeply, personalise every outreach, and build pipeline that converts.

Capabilities:
- Research and score prospects by fit, intent, and reachability
- Write hyper-personalised cold outreach emails and LinkedIn messages
- Build multi-touch outreach sequences with the right cadence
- Identify buying signals from company news, hiring, and tech stack
- Score prospect lists and surface the highest-priority targets
- Craft objection-handling scripts for common B2B pushbacks

Principles:
- Personalisation is the difference between spam and pipeline — research before outreach
- Lead scoring: ICP fit (40%) + intent signals (40%) + reachability (20%)
- The best hook uses a specific, recent, relevant detail about their company
- Short outreach beats long — get to the value proposition in 2 sentences
- Follow-up is where deals are made — 80% of responses come after touch 3+
- Never mass-blast — every message should feel 1:1

ICP signals: hiring in relevant roles, funding rounds, product launches, tech stack changes, competitor mentions

[STRICT SYSTEM RULES]
1. OUTPUT: Return ONLY raw JSON if requested. NO markdown (```json), NO filler.
2. REASONING: Think step-by-step internally, output final answer only.
3. DOMAIN: Decline out-of-scope tasks. Zero hallucinations.
4. TONE: Professional human employee. Never identify as AI/bot.

"""


class LeadHunterEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def score_prospect(self, prospect, instance=None) -> dict:
        prompt = f"""Score this B2B prospect for outreach priority.

Company: {prospect.company_name}
Contact: {prospect.contact_name or 'Unknown'}
Industry: {prospect.industry or 'Unknown'}
LinkedIn: {prospect.linkedin_url or 'Not available'}
Notes: {prospect.notes or 'No notes'}

Return JSON:
{{
  "score": integer 0-100,
  "icp_fit": "excellent|good|average|poor",
  "intent_signals": ["detected buying signals"],
  "best_hook": "personalised opening line for outreach",
  "ai_summary": "2-sentence prospect assessment",
  "recommended_channel": "email|linkedin|cold_call",
  "priority": "high|medium|low"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"score": 50, "icp_fit": "average", "intent_signals": [], "ai_summary": raw, "priority": "medium"}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"score_prospect for {prospect.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if res.get("score", 0) >= 90 or res.get("priority") == "high":
                raise PermissionRequired(
                    context=f"High-priority lead detected: {prospect.company_name}. Score: {res.get('score')}. Summary: {res.get('ai_summary')}",
                    option_a="Approve immediate high-priority outreach",
                    option_b="Deny (Nurture in standard queue)"
                )
        return res

    def draft_outreach(self, prospect, sequence_step: int = 1, channel: str = "email", instance=None) -> str:
        step_instructions = {
            1: "First touch: introduce yourself and the value proposition. Use their specific company context.",
            2: "Follow-up: reference the first message briefly. Add a different angle or social proof.",
            3: "Final follow-up: be direct about why you're reaching out. Include a simple, low-friction CTA.",
        }
        instruction = step_instructions.get(sequence_step, "Follow-up message")

        prompt = f"""Write a {channel} outreach message for this prospect (step {sequence_step} of 3).

Company: {prospect.company_name}
Contact: {prospect.contact_name or 'Decision maker'}
Industry: {prospect.industry or 'Unknown'}
Intent Summary: {prospect.ai_summary or 'B2B prospect'}

Instruction: {instruction}

Write ONLY the message body. For email: include subject line prefixed with 'SUBJECT:'. Keep it concise and personalised."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"draft_outreach step {sequence_step} for {prospect.pk}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def build_sequence(self, prospect, sequence_name: str, instance=None) -> list:
        prompt = f"""Build a complete outreach sequence for this prospect.

Company: {prospect.company_name}
Contact: {prospect.contact_name or 'Decision maker'}
Industry: {prospect.industry}
Notes: {prospect.notes or 'No notes'}

Return a JSON array of sequence steps:
{{
  "step": integer,
  "day": integer (day to send from start),
  "channel": "email|linkedin|call",
  "subject": "email subject if applicable",
  "message": "full message body",
  "goal": "what this step is trying to achieve"
}}

Create 5 touches: day 1, 3, 7, 14, 21."""

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
                action=f"build_sequence for {prospect.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def objection_response(self, objection: str, prospect_context: str, instance=None) -> str:
        prompt = f"""Write a response to this sales objection.

Objection: {objection}
Prospect context: {prospect_context}

Write a concise, confident response that:
1. Acknowledges the objection (don't dismiss it)
2. Reframes or provides evidence
3. Pivots to a next step
Keep it to 3-4 sentences maximum."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="objection_response",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
