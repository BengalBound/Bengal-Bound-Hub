import json
from agents.utils import agent_chat

SYSTEM_PROMPT = """You are Voice Receptionist, BengalBound's AI Phone Receptionist.

You handle inbound calls for businesses — booking appointments, answering FAQs, filtering spam, and routing urgent calls to human staff.

Capabilities:
- Detect caller intent: book, reschedule, cancel, FAQ, transfer, end call, spam, emergency
- Conduct natural multi-turn intake conversations via phone
- Generate appointment confirmation messages and follow-up scripts
- Analyse call transcripts for quality and conversion insights
- Produce weekly call performance reports

Principles:
- Every response is a phone call: be warm, concise, under 2 sentences per turn
- Emergency callers get transferred immediately — never make them wait
- Spam is detected early and ended politely
- Collect caller name, service, and preferred time before confirming any booking
- Always confirm details back to the caller before finalising"""


class VoiceReceptionistEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def analyse_call(self, transcript: str, business_name: str, business_type: str) -> dict:
        prompt = f"""Analyse this call transcript for a {business_type} business called {business_name}.

Transcript:
{transcript}

Return JSON:
{{
  "intent": "book_appointment|reschedule|cancel|faq|transfer_human|spam|emergency|end_call",
  "outcome": "booked|not_booked|transferred|spam_blocked|ended",
  "caller_sentiment": "positive|neutral|negative|frustrated",
  "quality_score": 0-100,
  "booking_probability": 0.0-1.0,
  "key_info_collected": {{"name": "", "service": "", "datetime": "", "phone": ""}},
  "missed_opportunities": ["what the receptionist could have done better"],
  "summary": "one-sentence call summary"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"intent": "unknown", "outcome": "unknown", "summary": raw}

    def generate_greeting(self, business_profile) -> str:
        prompt = f"""Write a warm, professional phone greeting for:
Business: {business_profile.business_name}
Type: {business_profile.get_business_type_display()}
Agent name: {business_profile.agent_name}

Keep it under 2 sentences. Friendly, professional, inviting."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return agent_chat(messages)

    def draft_confirmation_message(self, appointment) -> dict:
        prompt = f"""Write appointment confirmation messages for:

Business: {appointment.business.business_name}
Service: {appointment.service_type}
Date/Time: {appointment.scheduled_at.strftime("%A, %B %d at %I:%M %p")}
Caller name: {appointment.caller_name}

Return JSON:
{{
  "sms_text": "under 160 characters, friendly",
  "email_subject": "clear and specific",
  "email_body": "professional, includes date/time/service, cancellation note",
  "voice_confirmation": "what to say on the call to confirm"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"sms_text": raw, "email_subject": "Appointment Confirmed", "email_body": raw}

    def weekly_performance_report(self, business_name: str, stats: dict) -> str:
        prompt = f"""Write a weekly call performance report for {business_name}.

Stats:
- Total calls: {stats.get('total_calls', 0)}
- Appointments booked: {stats.get('booked', 0)}
- Spam blocked: {stats.get('spam', 0)}
- Transfers to staff: {stats.get('transfers', 0)}
- Avg call duration: {stats.get('avg_duration_sec', 0)}s
- Booking rate: {stats.get('booking_rate_pct', 0):.1f}%

Write a concise executive summary (3-4 sentences): what went well, what needs improvement, and one recommendation."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return agent_chat(messages)

    def spam_classification(self, transcript: str) -> dict:
        prompt = f"""Classify this call transcript as spam or legitimate.

Transcript: {transcript[:500]}

Return JSON:
{{
  "is_spam": true|false,
  "confidence": 0.0-1.0,
  "spam_indicators": ["list of specific phrases or patterns that indicate spam"],
  "recommended_action": "block|flag|allow"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"is_spam": False, "confidence": 0.0, "spam_indicators": [], "recommended_action": "allow"}
