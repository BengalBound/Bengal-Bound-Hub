import json
from agents.utils import agent_chat

SYSTEM_PROMPT = """You are Crux, BengalBound's AI CRM Manager.

Your role is to maximise pipeline velocity and close rate. You track every contact, score every lead, and ensure no opportunity goes cold.

Capabilities:
- Score contacts by purchase intent, engagement level, and fit
- Generate personalised follow-up strategies per contact
- Analyse pipeline health and flag at-risk deals
- Draft personalised outreach emails and call scripts
- Detect dormant contacts and recommend re-engagement
- Provide weekly pipeline health reports

Principles:
- Every contact deserves a personalised, timely follow-up
- Intent signals matter more than demographics
- A dormant lead isn't lost — it needs the right trigger
- Pipeline reports should show velocity, not just volume
- Track sentiment across interactions to predict close probability
- Never let a high-intent contact go more than 72 hours without touch

Pipeline stages: prospect → qualified → proposal → negotiation → won → lost"""


class CruxEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def score_contact(self, contact, interactions: list) -> dict:
        interaction_summary = "\n".join(
            f"- [{i.interaction_type}] {i.summary} (sentiment: {i.sentiment}, date: {i.occurred_at.date()})"
            for i in interactions[:10]
        )
        prompt = f"""Score this CRM contact by purchase intent and engagement.

Contact: {contact.name} at {contact.company}
Pipeline Stage: {contact.pipeline_stage or 'unknown'}
Last Activity: {contact.last_activity}
Is Cold: {contact.is_cold}

Interaction History:
{interaction_summary or 'No interactions recorded'}

Return JSON:
{{
  "intent_score": integer 0-100,
  "engagement_level": "cold|warm|hot",
  "close_probability": float 0-1,
  "next_best_action": "specific action to take",
  "ai_summary": "2-sentence contact assessment",
  "risk_flags": ["any risks or concerns"]
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"intent_score": 50, "engagement_level": "warm", "close_probability": 0.3,
                    "next_best_action": raw, "ai_summary": "", "risk_flags": []}

    def follow_up_plan(self, contact) -> dict:
        prompt = f"""Create a follow-up plan for this contact.

Name: {contact.name}
Company: {contact.company}
Stage: {contact.pipeline_stage or 'prospect'}
Intent Score: {contact.intent_score or 'unknown'}
AI Summary: {contact.ai_summary or 'No summary available'}

Return JSON:
{{
  "sequence": [
    {{"day": 1, "channel": "email|call|linkedin", "action": "what to do", "message_draft": "..."}},
    ...
  ],
  "key_talking_points": ["list of points"],
  "objection_responses": {{"objection": "response"}}
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"sequence": [], "key_talking_points": [], "objection_responses": {}}

    def pipeline_health_report(self, contacts: list) -> str:
        stages = {}
        for c in contacts:
            stage = c.pipeline_stage or "unqualified"
            stages[stage] = stages.get(stage, 0) + 1

        stage_summary = "\n".join(f"- {stage}: {count}" for stage, count in stages.items())
        cold_count = sum(1 for c in contacts if c.is_cold)

        prompt = f"""Generate a pipeline health report.

Pipeline Summary:
{stage_summary}
Total contacts: {len(contacts)}
Cold/dormant: {cold_count}

Provide:
1. Pipeline health score (0-100) with reasoning
2. Top 3 risks to this month's targets
3. Recommended actions to unblock pipeline
4. Contacts to prioritise this week"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return agent_chat(messages)

    def re_engagement_message(self, contact) -> str:
        prompt = f"""Write a re-engagement message for a dormant contact.

Name: {contact.name}
Company: {contact.company}
Last Activity: {contact.last_activity}
Previous Summary: {contact.ai_summary or 'No history available'}

Write a short, personal re-engagement email (not salesy). Reference past context if available. Include a low-friction CTA."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return agent_chat(messages)
