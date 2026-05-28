"""
voice_receptionist/ai_engine.py
---------------------------------
Gemini 1.5 Flash NLU engine for intent detection and conversation management.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from agents.utils import ai_chat

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Intent Enum
# ---------------------------------------------------------------------------

class Intent(str, Enum):
    BOOK_APPOINTMENT   = "book_appointment"
    RESCHEDULE         = "reschedule"
    CANCEL             = "cancel"
    FAQ                = "faq"
    TRANSFER_HUMAN     = "transfer_human"
    END_CALL           = "end_call"
    COLLECT_MORE_INFO  = "collect_more_info"
    SPAM_DETECTED      = "spam_detected"
    EMERGENCY          = "emergency"


EMERGENCY_KEYWORDS = [
    "emergency", "urgent", "pain", "bleeding", "accident",
    "critical", "help me", "dying", "fire", "burst pipe",
]

SPAM_KEYWORDS = [
    "reduce your mortgage", "irs warrant", "social security",
    "car warranty", "extended warranty", "free cruise",
    "you've been selected", "government grant", "student loan forgiveness",
    "press 1 to speak", "debt consolidation",
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class IntentResult:
    intent: Intent
    response_text: str
    collected_data: dict = field(default_factory=dict)
    next_action: str = "gather"          # gather | hangup | transfer | book
    confidence: float = 1.0


# ---------------------------------------------------------------------------
# Prompt Templates (per business type)
# ---------------------------------------------------------------------------

INTAKE_QUESTIONS = {
    "plumber": [
        "What plumbing issue are you experiencing?",
        "What is the address where the service is needed?",
        "What is your preferred date and time for the appointment?",
    ],
    "dentist": [
        "Are you a new or existing patient?",
        "What is the reason for your visit today?",
        "Do you have dental insurance, and if so, what carrier?",
        "What is your preferred date and time?",
    ],
    "salon": [
        "What service are you interested in today?",
        "Do you have a preferred stylist or staff member?",
        "What is your preferred date and time?",
    ],
    "general": [
        "What service do you need help with?",
        "What is your preferred date and time for the appointment?",
    ],
}


def _build_system_prompt(business_profile, session_history: list[dict]) -> str:
    intake_qs = "\n".join(
        f"- {q}" for q in INTAKE_QUESTIONS.get(business_profile.business_type, INTAKE_QUESTIONS["general"])
    )
    from django.utils import timezone
    now = timezone.localtime()
    is_open = business_profile.is_open_now()

    return f"""You are {business_profile.agent_name}, the AI receptionist for {business_profile.business_name}, a {business_profile.get_business_type_display()} business.

Current date and time: {now.strftime("%A, %B %d %Y, %I:%M %p")}
Business is currently: {"OPEN" if is_open else "CLOSED — you may still book future appointments"}
Services offered: {", ".join(business_profile.services_offered) or "General services"}

Your job:
1. Greet the caller warmly.
2. Identify their intent (book, reschedule, cancel, question, or transfer to staff).
3. Ask these intake questions one at a time as needed:
{intake_qs}
4. Confirm all collected details with the caller before finalizing.
5. Be concise — this is a phone call. Keep responses under 2 sentences per turn.

ALWAYS respond with valid JSON only. No prose outside JSON.
JSON format:
{{
  "intent": "<one of: book_appointment | reschedule | cancel | faq | transfer_human | end_call | collect_more_info | spam_detected | emergency>",
  "response_text": "<what to say to the caller>",
  "collected_data": {{
    "caller_name": "",
    "service_type": "",
    "preferred_datetime": "",
    "address": "",
    "insurance_type": "",
    "preferred_staff": "",
    "notes": ""
  }},
  "next_action": "<gather | hangup | transfer | book>",
  "confidence": 0.0
}}"""


# ---------------------------------------------------------------------------
# Main engine function
# ---------------------------------------------------------------------------

def detect_intent(
    latest_transcript: str,
    session_history: list[dict],
    business_profile,
) -> IntentResult:
    """
    Detect caller intent via ai_chat() (routes to Gemini/OpenAI/mock per AI_PROVIDER).
    Fast-path keyword checks run before any AI call.
    """
    lower = latest_transcript.lower()

    for kw in EMERGENCY_KEYWORDS:
        if kw in lower:
            return IntentResult(
                intent=Intent.EMERGENCY,
                response_text="I understand this is urgent. Let me connect you with a team member right away. Please hold.",
                next_action="transfer",
            )

    if check_spam_keywords(lower):
        return IntentResult(
            intent=Intent.SPAM_DETECTED,
            response_text="Thank you for calling. Have a great day!",
            next_action="hangup",
            confidence=0.9,
        )

    system_prompt = _build_system_prompt(business_profile, session_history)
    messages = [{"role": "user", "content": latest_transcript}]

    # Use business profile ID as proxy for organization_id (Voice Receptionist rate limiting)
    org_id = hash(business_profile.firebase_uid) % (10 ** 8) if business_profile else None

    raw = ""
    try:
        raw = ai_chat(
            system_prompt=system_prompt,
            messages=messages,
            organization_id=org_id
        )
        data = json.loads(raw.strip())
        return IntentResult(
            intent=Intent(data.get("intent", Intent.COLLECT_MORE_INFO)),
            response_text=data.get("response_text", "Could you repeat that?"),
            collected_data=data.get("collected_data", {}),
            next_action=data.get("next_action", "gather"),
            confidence=float(data.get("confidence", 0.8)),
        )
    except json.JSONDecodeError as e:
        logger.error("AI returned invalid JSON: %s | raw: %s", e, raw[:200])
        return _fallback_result()
    except Exception as e:
        logger.error("AI call error in detect_intent: %s", e)
        return _fallback_result()


def check_spam_keywords(transcript_lower: str) -> bool:
    """Fast keyword check — returns True if transcript contains known spam phrases."""
    return any(kw in transcript_lower for kw in SPAM_KEYWORDS)


def _fallback_result() -> IntentResult:
    return IntentResult(
        intent=Intent.COLLECT_MORE_INFO,
        response_text="I'm sorry, I didn't quite catch that. Could you say that again?",
        next_action="gather",
        confidence=0.0,
    )
