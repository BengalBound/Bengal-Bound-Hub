"""
voice_receptionist/tests/test_spam_filter.py
--------------------------------------------
Unit tests for the spam detection pipeline.
"""

from django.test import TestCase
from unittest.mock import patch
from agents.voice_receptionist.models import BusinessProfile, SpamLog, SpamBlocklist, BusinessType
from agents.voice_receptionist.spam_filter import run_spam_check, handle_silence_timeout, SpamResult


def make_business():
    return BusinessProfile.objects.create(
        firebase_uid="spam-filter-test-uid",
        business_name="Filter Test Biz",
        business_type=BusinessType.GENERAL,
        phone="+15550000001",
        twilio_phone_number="+15550000099",
    )


class SpamFilterTest(TestCase):
    def setUp(self):
        self.biz = make_business()

    def test_clean_number_passes(self):
        result = run_spam_check("+15551234567", self.biz)
        self.assertEqual(result.result, SpamResult.CLEAN)
        self.assertEqual(result.action, "allow")

    def test_blacklisted_number_blocked(self):
        SpamLog.objects.create(
            business=self.biz,
            caller_phone="+15550000000",
            detection_reason="manual",
            action_taken="disconnected",
            is_blacklisted=True,
        )
        result = run_spam_check("+15550000000", self.biz)
        self.assertEqual(result.result, SpamResult.CONFIRMED_SPAM)
        self.assertEqual(result.action, "disconnect")

    def test_whitelisted_number_passes(self):
        SpamLog.objects.create(
            business=self.biz,
            caller_phone="+15550000000",
            detection_reason="manual",
            action_taken="allowed",
            is_whitelisted=True,
        )
        result = run_spam_check("+15550000000", self.biz)
        self.assertEqual(result.result, SpamResult.CLEAN)

    def test_community_blocklist_blocks(self):
        SpamBlocklist.objects.create(phone_number="+15550001111")
        result = run_spam_check("+15550001111", self.biz)
        self.assertEqual(result.result, SpamResult.CONFIRMED_SPAM)

    def test_spam_keyword_in_transcript(self):
        result = run_spam_check("+15559999999", self.biz, transcript="reduce your mortgage rate today")
        self.assertEqual(result.result, SpamResult.LIKELY_SPAM)
        self.assertEqual(result.action, "flag")

    def test_silence_timeout(self):
        result = handle_silence_timeout("+15550002222", self.biz)
        self.assertEqual(result.result, SpamResult.SILENCE)
        self.assertEqual(result.action, "disconnect")
        # Verify SpamLog was written
        self.assertTrue(SpamLog.objects.filter(caller_phone="+15550002222").exists())

    def test_spam_log_written_on_block(self):
        SpamBlocklist.objects.create(phone_number="+15553333333")
        run_spam_check("+15553333333", self.biz)
        self.assertTrue(SpamLog.objects.filter(caller_phone="+15553333333").exists())
