"""
voice_receptionist/tests/test_api_endpoints.py
------------------------------------------------
Integration tests for all DRF API endpoints.
URL base: /hub/<slug>/agents/voice-receptionist/
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from agents.voice_receptionist.models import (
    BusinessProfile, Call, Appointment, UserProfile, BusinessType,
)

User = get_user_model()

# VR is mounted at /hub/<slug>/agents/voice-receptionist/ in the root urlconf.
# The slug is just a routing segment; VR views use their own BusinessProfile model.
BASE = "/hub/test-biz/agents/voice-receptionist"


def make_admin_client():
    """Create a test user + VR UserProfile with admin role and return an authenticated APIClient."""
    user = User.objects.create_user(username="firebase-admin-uid", email="admin@test.com")
    biz = BusinessProfile.objects.create(
        firebase_uid="firebase-admin-uid",
        business_name="API Test Biz",
        business_type=BusinessType.SALON,
        phone="+15550000001",
        twilio_phone_number="+15550000097",
    )
    UserProfile.objects.create(user=user, firebase_uid="firebase-admin-uid", role="admin", business=biz)

    client = APIClient()
    client.force_authenticate(user=user)
    return client, user, biz


class BusinessProfileAPITest(TestCase):
    def setUp(self):
        self.client, self.user, self.biz = make_admin_client()

    def test_list_profiles(self):
        response = self.client.get(f"{BASE}/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_profile(self):
        response = self.client.get(f"{BASE}/profile/{self.biz.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["business_name"], "API Test Biz")

    def test_update_profile(self):
        response = self.client.patch(
            f"{BASE}/profile/{self.biz.id}/",
            {"agent_name": "Bella"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.biz.refresh_from_db()
        self.assertEqual(self.biz.agent_name, "Bella")

    def test_voices_endpoint(self):
        response = self.client.get(f"{BASE}/profile/voices/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)


class AppointmentAPITest(TestCase):
    def setUp(self):
        self.client, self.user, self.biz = make_admin_client()

    def test_create_appointment(self):
        payload = {
            "business": str(self.biz.id),
            "caller_name": "Test Client",
            "caller_phone": "+15551234567",
            "service_type": "Haircut",
            "scheduled_at": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            "status": "confirmed",
        }
        with patch("agents.voice_receptionist.calendar_sync.create_appointment_event", return_value="fake_event_id"), \
             patch("agents.voice_receptionist.notifications.notify_appointment"):
            response = self.client.post(f"{BASE}/appointments/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_list_appointments(self):
        Appointment.objects.create(
            business=self.biz,
            caller_name="List Test",
            caller_phone="+1555",
            service_type="Color",
            scheduled_at=timezone.now() + timezone.timedelta(days=2),
        )
        response = self.client.get(f"{BASE}/appointments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data if isinstance(response.data, list) else response.data.get("results", [])
        self.assertEqual(len(data), 1)

    def test_upcoming_appointments(self):
        Appointment.objects.create(
            business=self.biz,
            caller_name="Upcoming",
            caller_phone="+1556",
            service_type="Nails",
            scheduled_at=timezone.now() + timezone.timedelta(days=3),
        )
        response = self.client.get(f"{BASE}/appointments/upcoming/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_booking_past_date_rejected(self):
        payload = {
            "business": str(self.biz.id),
            "caller_name": "Past Client",
            "caller_phone": "+15559999999",
            "service_type": "Haircut",
            "scheduled_at": (timezone.now() - timezone.timedelta(hours=1)).isoformat(),
            "status": "confirmed",
        }
        response = self.client.post(f"{BASE}/appointments/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CallAPITest(TestCase):
    def setUp(self):
        self.client, self.user, self.biz = make_admin_client()

    def test_list_calls(self):
        Call.objects.create(business=self.biz, call_sid="CAlist001", caller_phone="+1555")
        response = self.client.get(f"{BASE}/calls/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_active_calls_endpoint(self):
        Call.objects.create(business=self.biz, call_sid="CAactive001", caller_phone="+1556", status="ongoing")
        response = self.client.get(f"{BASE}/calls/active/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)


class AnalyticsAPITest(TestCase):
    def setUp(self):
        self.client, self.user, self.biz = make_admin_client()

    def test_analytics_endpoint(self):
        response = self.client.get(f"{BASE}/analytics/?range=30")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_calls", response.data)
        self.assertIn("booking_rate_pct", response.data)
