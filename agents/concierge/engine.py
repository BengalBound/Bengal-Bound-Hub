import json
from agents.utils import agent_chat

SYSTEM_PROMPT = """You are Concierge, BengalBound's AI Client Reception and Routing Specialist.

Your role is to be the perfect first impression — warm, professional, and effortlessly efficient. You handle every inbound interaction so the right person responds at the right time.

Capabilities:
- Triage inbound emails by category, priority, and intent
- Schedule and confirm meeting requests intelligently
- Draft professional responses for common inquiry types
- Route requests to the correct department or person
- Qualify meeting requests before they reach the calendar
- Handle basic FAQs without human involvement

Principles:
- Every person deserves a prompt, warm, professional response
- Route, don't hoard — get the right person involved quickly
- Meeting requests should be confirmed with context and agenda
- Flag anything that requires urgent attention
- Spam/irrelevant requests should be politely declined

Categories: inquiry, sales, support, complaint, newsletter, internal, spam, partnership, media, job_application"""


class ConciergeEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def triage_email(self, email) -> dict:
        prompt = f"""Triage this inbound email for a business.

From: {email.sender}
Subject: {email.subject}
Body preview: {email.body_preview}

Return JSON:
{{
  "category": "inquiry|sales|support|complaint|newsletter|internal|spam|partnership|media|job_application",
  "priority": "low|medium|high|urgent",
  "intent_summary": "1-sentence summary of what they want",
  "routing": "which team/person should handle this",
  "suggested_reply": "brief reply draft if this is straightforward",
  "needs_human": boolean
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"category": "inquiry", "priority": "medium", "needs_human": True}

    def schedule_meeting(self, meeting_request) -> dict:
        attendees = ", ".join(meeting_request.attendees) if meeting_request.attendees else "Not specified"
        times = json.dumps(meeting_request.preferred_times) if meeting_request.preferred_times else "Flexible"

        prompt = f"""Process this meeting request and prepare a confirmation.

Title: {meeting_request.title}
Description: {meeting_request.description}
Requested By / Attendees: {attendees}
Preferred Times: {times}

Return JSON:
{{
  "confirmation_message": "the message to send confirming the meeting",
  "agenda_suggestion": "suggested agenda items",
  "prep_notes": "what the host should prepare",
  "calendar_description": "description for the calendar invite"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"confirmation_message": raw, "agenda_suggestion": "", "prep_notes": "", "calendar_description": ""}

    def compose_reply(self, email, routing_context: str = "") -> str:
        prompt = f"""Draft a professional reply to this inbound email.

From: {email.sender}
Subject: {email.subject}
Message: {email.body_preview}
Category: {email.category}
Priority: {email.priority}
Routing context: {routing_context}

Write ONLY the reply body — professional, warm, concise. Include a clear next step."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return agent_chat(messages)

    def qualify_meeting_request(self, request) -> dict:
        prompt = f"""Evaluate if this meeting request should proceed.

Title: {request.title}
Description: {request.description}
Attendees: {request.attendees}

Return JSON:
{{
  "qualified": boolean,
  "reason": "why qualified or not",
  "questions_to_ask": ["list of clarifying questions if needed"],
  "suggested_duration_minutes": integer
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"qualified": True, "reason": raw, "questions_to_ask": [], "suggested_duration_minutes": 30}
