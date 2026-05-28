"""
voice_receptionist/tests/test_ai_engine.py
-------------------------------------------
Unit tests for the Gemini 1.5 Flash AI engine.
Gemini API calls are mocked — no actual API usage during tests.
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock
from agents.voice_receptionist.models import BusinessProfile, BusinessType
from agents.voice_receptionist.ai_engine import detect_intent, check_spam_keywords, Intent, IntentResult


def make_business():
    return BusinessProfile.objects.create(
        firebase_uid="ai-engine-test-uid",
        business_name="Sparkle Salon",
        business_type=BusinessType.SALON,
        phone="+15550000001",
        twilio_phone_number="+15550000098",
        agent_name="Aria",
        services_offered=["Haircut", "Color", "Nails"],
    )


MOCK_BOOKING_RESPONSE = {
    "intent": "book_appointment",
    "response_text": "I'd be happy to book that for you. What day works best?",
    "collected_data": {"service_type": "Haircut"},
    "next_action": "gather",
    "confidence": 0.92,
}

MOCK_TRANSFER_RESPONSE = {
    "intent": "transfer_human",
    "response_text": "Let me connect you with a team member.",
    "collected_data": {},
    "next_action": "transfer",
    "confidence": 0.95,
}


class CheckSpamKeywordsTest(TestCase):
    def test_spam_keyword_detected(self):
        self.assertTrue(check_spam_keywords("reduce your mortgage rate today"))

    def test_irs_warrant_keyword(self):
        self.assertTrue(check_spam_keywords("there is an irs warrant for your arrest"))

    def test_clean_speech_passes(self):
        self.assertFalse(check_spam_keywords("I would like to book a haircut appointment"))

    def test_empty_string(self):
        self.assertFalse(check_spam_keywords(""))


class DetectIntentTest(TestCase):
    def setUp(self):
        self.business = make_business()

    @patch("agents.voice_receptionist.ai_engine.ai_chat")
    def test_booking_intent_detected(self, mock_ai_chat):
        import json
        mock_ai_chat.return_value = json.dumps(MOCK_BOOKING_RESPONSE)

        result = detect_intent("I'd like to book a haircut", [], self.business)
        self.assertEqual(result.intent, Intent.BOOK_APPOINTMENT)
        self.assertEqual(result.next_action, "gather")
        self.assertEqual(result.collected_data.get("service_type"), "Haircut")

    @patch("agents.voice_receptionist.ai_engine.ai_chat")
    def test_transfer_intent_detected(self, mock_ai_chat):
        import json
        mock_ai_chat.return_value = json.dumps(MOCK_TRANSFER_RESPONSE)

        result = detect_intent("Can I speak with a person?", [], self.business)
        self.assertEqual(result.intent, Intent.TRANSFER_HUMAN)
        self.assertEqual(result.next_action, "transfer")

    def test_emergency_keyword_bypasses_gemini(self):
        """Emergency keywords should short-circuit before calling Gemini."""
        result = detect_intent("I have an emergency, there's blood everywhere!", [], self.business)
        self.assertEqual(result.intent, Intent.EMERGENCY)
        self.assertEqual(result.next_action, "transfer")

    def test_spam_keyword_bypasses_gemini(self):
        """Spam keywords should short-circuit before calling Gemini."""
        result = detect_intent("reduce your mortgage rate today", [], self.business)
        self.assertEqual(result.intent, Intent.SPAM_DETECTED)
        self.assertEqual(result.next_action, "hangup")

    @patch("agents.voice_receptionist.ai_engine.ai_chat")
    def test_invalid_json_returns_fallback(self, mock_ai_chat):
        """Invalid JSON from Gemini should return a safe fallback."""
        mock_ai_chat.return_value = "This is not valid JSON { broken"

        result = detect_intent("Hello there", [], self.business)
        self.assertEqual(result.intent, Intent.COLLECT_MORE_INFO)
        self.assertEqual(result.confidence, 0.0)

    @patch("agents.voice_receptionist.ai_engine.ai_chat")
    def test_api_error_returns_fallback(self, mock_ai_chat):
        """API errors should return a safe fallback."""
        mock_ai_chat.side_effect = Exception("API quota exceeded")

        result = detect_intent("Hi there", [], self.business)
        self.assertEqual(result.intent, Intent.COLLECT_MORE_INFO)
        self.assertEqual(result.confidence, 0.0)
