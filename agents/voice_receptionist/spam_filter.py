"""
voice_receptionist/spam_filter.py
-----------------------------------
Multi-layer spam and robocall detection engine.

Layers (in order of cost):
 1. Blacklist DB lookup         — free, instant
 2. Community blocklist         — free, instant
 3. Silence detection           — handled via Twilio <Gather> timeout (see twilio_handler)
 4. AI keyword detection        — Gemini (no extra API cost, uses free tier)
 5. VOIP flag                   — optional Twilio Lookup (off by default)
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class SpamResult(str, Enum):
    CLEAN           = "clean"
    CONFIRMED_SPAM  = "confirmed_spam"
    LIKELY_SPAM     = "likely_spam"
    SILENCE         = "silence"


@dataclass
class SpamCheckResult:
    result: SpamResult
    reason: str
    action: str   # "disconnect" | "flag" | "allow"
    confidence: float = 1.0


def run_spam_check(
    caller_phone: str,
    business,
    transcript: Optional[str] = None,
) -> SpamCheckResult:
    """
    Full spam check pipeline.

    Args:
        caller_phone: Normalized E.164 phone number string.
        business:     BusinessProfile instance.
        transcript:   Optional partial transcript for keyword check.

    Returns:
        SpamCheckResult with recommended action.
    """
    from .models import SpamLog, SpamBlocklist

    # ------------------------------------------------------------------
    # Layer 1: Business-specific whitelist (always passes)
    # ------------------------------------------------------------------
    if SpamLog.objects.filter(
        business=business, caller_phone=caller_phone, is_whitelisted=True
    ).exists():
        return SpamCheckResult(SpamResult.CLEAN, "whitelisted", "allow", 1.0)

    # ------------------------------------------------------------------
    # Layer 2: Business-specific blacklist
    # ------------------------------------------------------------------
    if SpamLog.objects.filter(
        business=business, caller_phone=caller_phone, is_blacklisted=True
    ).exists():
        _log_spam(caller_phone, business, "Business blacklist", "disconnected")
        return SpamCheckResult(SpamResult.CONFIRMED_SPAM, "Business blacklist match", "disconnect", 1.0)

    # ------------------------------------------------------------------
    # Layer 3: Community blocklist
    # ------------------------------------------------------------------
    if SpamBlocklist.objects.filter(phone_number=caller_phone).exists():
        _log_spam(caller_phone, business, "Community spam blocklist", "disconnected")
        return SpamCheckResult(SpamResult.CONFIRMED_SPAM, "Community blocklist match", "disconnect", 0.95)

    # ------------------------------------------------------------------
    # Layer 4: AI keyword check (if transcript is available)
    # ------------------------------------------------------------------
    if transcript:
        from .ai_engine import check_spam_keywords
        if check_spam_keywords(transcript.lower()):
            _log_spam(caller_phone, business, "AI keyword detection", "flagged", transcript[:200])
            return SpamCheckResult(
                SpamResult.LIKELY_SPAM,
                "AI detected spam keywords in transcript",
                "flag",
                0.80,
            )

    return SpamCheckResult(SpamResult.CLEAN, "No spam signals detected", "allow", 1.0)


def handle_silence_timeout(caller_phone: str, business) -> SpamCheckResult:
    """
    Called when Twilio <Gather> times out with no audio from the caller.
    Auto-classifies as robocall (silence = autodialer pattern).
    """
    _log_spam(caller_phone, business, "Silence/no-audio within 3 seconds", "disconnected")
    return SpamCheckResult(
        SpamResult.SILENCE,
        "Caller silent within 3 seconds — likely autodialer",
        "disconnect",
        0.85,
    )


def _log_spam(
    caller_phone: str,
    business,
    reason: str,
    action: str,
    transcript_snippet: str = "",
):
    """Write a SpamLog entry to the database."""
    from .models import SpamLog, SpamAction
    action_map = {
        "disconnected": SpamAction.DISCONNECTED,
        "flagged":      SpamAction.FLAGGED,
        "allowed":      SpamAction.ALLOWED,
    }
    try:
        SpamLog.objects.create(
            business=business,
            caller_phone=caller_phone,
            detection_reason=reason,
            action_taken=action_map.get(action, SpamAction.FLAGGED),
            transcript_snippet=transcript_snippet,
        )
    except Exception as e:
        logger.error("Failed to write SpamLog: %s", e)
