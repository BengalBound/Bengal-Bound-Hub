"""
voice_receptionist/tests/test_models.py
-----------------------------------------
Unit tests for all Voice Receptionist Django models.
Uses SQLite (Django TEST config) — zero external dependencies.
"""

from datetime import time
from django.test import TestCase
from django.utils import timezone
from agents.voice_receptionist.models import (
    BusinessProfile, Call, Appointment, SpamLog, SpamBlocklist,
    UserProfile, NotificationTemplate, BusinessType, CallStatus, AppointmentStatus,
)


def make_business(**kwargs):
    defaults = dict(
        firebase_uid="test-uid-001",
        business_name="Test Salon",
        business_type=BusinessType.SALON,
        phone="+15551234567",
        forwarding_number="+15559999999",
        twilio_phone_number="+15550000001",
    )
    defaults.update(kwargs)
    return BusinessProfile.objects.create(**defaults)


class BusinessProfileModelTest(TestCase):
    def setUp(self):
        self.biz = make_business()

    def test_str(self):
        self.assertIn("Test Salon", str(self.biz))

    def test_is_open_now_no_hours(self):
        """Without hours config, is_open_now should return False."""
        self.assertFalse(self.biz.is_open_now())

    def test_is_open_during_configured_hours(self):
        """Business configured 00:00–23:59 every day should always be open."""
        from datetime import datetime
        days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        hours = {d: {"open": "00:00", "close": "23:59"} for d in days}
        self.biz.business_hours = hours
        self.biz.save()
        self.assertTrue(self.biz.is_open_now())


class CallModelTest(TestCase):
    def setUp(self):
        self.biz = make_business(firebase_uid="call-uid-001", twilio_phone_number="+15550000002")

    def test_create_call(self):
        call = Call.objects.create(
            business=self.biz,
            call_sid="CAtest12345",
            caller_phone="+15551112222",
            status=CallStatus.ONGOING,
        )
        self.assertEqual(Call.objects.count(), 1)
        self.assertIn("CAtest12345", str(call.call_sid))

    def test_call_str(self):
        call = Call.objects.create(
            business=self.biz, call_sid="CAtest99999", caller_phone="+15553334444", status="completed"
        )
        self.assertIn("+15553334444", str(call))

    def test_call_sid_unique(self):
        from django.db import IntegrityError
        Call.objects.create(business=self.biz, call_sid="CAunique001", caller_phone="+1555")
        with self.assertRaises(IntegrityError):
            Call.objects.create(business=self.biz, call_sid="CAunique001", caller_phone="+1556")


class AppointmentModelTest(TestCase):
    def setUp(self):
        self.biz = make_business(firebase_uid="appt-uid-001", twilio_phone_number="+15550000003")

    def test_create_appointment(self):
        appt = Appointment.objects.create(
            business=self.biz,
            caller_name="Jane Doe",
            caller_phone="+15551234567",
            service_type="Haircut",
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            status=AppointmentStatus.CONFIRMED,
        )
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertIn("Jane Doe", str(appt))

    def test_appointment_status_default(self):
        appt = Appointment.objects.create(
            business=self.biz,
            caller_name="Bob",
            caller_phone="+1555",
            service_type="Color",
            scheduled_at=timezone.now() + timezone.timedelta(hours=3),
        )
        self.assertEqual(appt.status, AppointmentStatus.CONFIRMED)


class SpamLogModelTest(TestCase):
    def setUp(self):
        self.biz = make_business(firebase_uid="spam-uid-001", twilio_phone_number="+15550000004")

    def test_create_spam_log(self):
        log = SpamLog.objects.create(
            business=self.biz,
            caller_phone="+15550000000",
            detection_reason="Community blocklist match",
            action_taken="disconnected",
        )
        self.assertEqual(SpamLog.objects.count(), 1)
        self.assertIn("+15550000000", str(log))

    def test_whitelist_flag(self):
        log = SpamLog.objects.create(
            business=self.biz,
            caller_phone="+15550000001",
            detection_reason="Test",
            action_taken="flagged",
        )
        log.is_whitelisted = True
        log.save()
        self.assertTrue(SpamLog.objects.get(id=log.id).is_whitelisted)


class SpamBlocklistModelTest(TestCase):
    def test_create_and_unique(self):
        from django.db import IntegrityError
        SpamBlocklist.objects.create(phone_number="+10000000000")
        with self.assertRaises(IntegrityError):
            SpamBlocklist.objects.create(phone_number="+10000000000")
