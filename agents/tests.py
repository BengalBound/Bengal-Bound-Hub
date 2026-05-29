import json
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from hub.models import BusinessInstance, BusinessEmployee
from agents.aria.models import SupportTicket, TicketResponse
from agents.crux.models import Contact
from agents.mira.models import ClientHealth
from agents.lead_hunter.models import Prospect

User = get_user_model()

class AgentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create Users first
        self.user_a = User.objects.create_user(
            username="user_a",
            email="user_a@example.com",
            password="password123"
        )
        self.user_b = User.objects.create_user(
            username="user_b",
            email="user_b@example.com",
            password="password123"
        )

        # Create Tenant A
        self.biz_a = BusinessInstance.objects.create(
            owner=self.user_a,
            name="Company A",
            slug="company-a",
            is_active=True
        )
        self.emp_a = BusinessEmployee.objects.create(
            business=self.biz_a,
            user=self.user_a,
            name="Employee A",
            is_active=True
        )

        # Create Tenant B
        self.biz_b = BusinessInstance.objects.create(
            owner=self.user_b,
            name="Company B",
            slug="company-b",
            is_active=True
        )
        self.emp_b = BusinessEmployee.objects.create(
            business=self.biz_b,
            user=self.user_b,
            name="Employee B",
            is_active=True
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Tenant Access Controls
    # ─────────────────────────────────────────────────────────────────────────

    def test_anonymous_user_is_blocked(self):
        url = reverse("aria:tickets-list", kwargs={"slug": self.biz_a.slug})
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_other_tenant_user_is_blocked(self):
        self.client.force_authenticate(user=self.user_b)
        url = reverse("aria:tickets-list", kwargs={"slug": self.biz_a.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # ─────────────────────────────────────────────────────────────────────────
    # Aria Agent Endpoints
    # ─────────────────────────────────────────────────────────────────────────

    def test_aria_ticket_lifecycle(self):
        self.client.force_authenticate(user=self.user_a)

        # 1. Create a support ticket
        url = reverse("aria:tickets-list", kwargs={"slug": self.biz_a.slug})
        data = {
            "subject": "Missing delivery item",
            "description": "My item hasn't arrived yet.",
            "priority": "high",
            "channel": "email"
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SupportTicket.objects.count(), 1)
        ticket = SupportTicket.objects.first()
        self.assertEqual(ticket.subject, "Missing delivery item")
        self.assertEqual(ticket.business, self.biz_a)

        # 2. Get list of tickets
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["subject"], "Missing delivery item")

        # 3. Suggest a reply using mocked agent_chat
        suggest_url = reverse("aria:tickets-suggest-response", kwargs={
            "slug": self.biz_a.slug,
            "pk": str(ticket.id)
        })
        with patch("agents.aria.views.agent_chat", return_value="Hello! We are looking into this.") as mock_chat:
            resp = self.client.post(suggest_url)
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
            mock_chat.assert_called_once()
            self.assertEqual(TicketResponse.objects.count(), 1)
            response_obj = TicketResponse.objects.first()
            self.assertEqual(response_obj.content, "Hello! We are looking into this.")
            self.assertTrue(response_obj.is_ai_generated)

    # ─────────────────────────────────────────────────────────────────────────
    # Crux Agent Endpoints
    # ─────────────────────────────────────────────────────────────────────────

    def test_crux_score_lifecycle(self):
        self.client.force_authenticate(user=self.user_a)

        # Create contact
        contact = Contact.objects.create(
            business=self.biz_a,
            name="John Doe",
            company="Doe Enterprises",
            pipeline_stage="discovery",
            is_cold=True
        )

        score_url = reverse("crux:contacts-score", kwargs={
            "slug": self.biz_a.slug,
            "pk": str(contact.id)
        })

        mock_payload = json.dumps({
            "intent_score": 85,
            "ai_summary": "Extremely hot lead. Ready to buy."
        })

        with patch("agents.crux.views.agent_chat", return_value=mock_payload) as mock_chat:
            resp = self.client.post(score_url)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            mock_chat.assert_called_once()
            contact.refresh_from_db()
            self.assertEqual(contact.intent_score, 85)
            self.assertEqual(contact.ai_summary, "Extremely hot lead. Ready to buy.")

    # ─────────────────────────────────────────────────────────────────────────
    # Mira Agent Endpoints
    # ─────────────────────────────────────────────────────────────────────────

    def test_mira_churn_prediction(self):
        self.client.force_authenticate(user=self.user_a)

        health = ClientHealth.objects.create(
            business=self.biz_a,
            health_score=80,
            risk_level="healthy",
            login_frequency=5.0,
            feature_usage=75.0,
            open_tickets=1
        )

        churn_url = reverse("mira:health-predict-churn", kwargs={
            "slug": self.biz_a.slug,
            "pk": str(health.id)
        })

        mock_payload = json.dumps({
            "churn_probability": 0.12,
            "ai_summary": "Client is healthy, feature adoption is high."
        })

        with patch("agents.mira.views.agent_chat", return_value=mock_payload) as mock_chat:
            resp = self.client.post(churn_url)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            mock_chat.assert_called_once()
            health.refresh_from_db()
            self.assertAlmostEqual(health.churn_probability, 0.12)
            self.assertEqual(health.ai_summary, "Client is healthy, feature adoption is high.")

    # ─────────────────────────────────────────────────────────────────────────
    # Lead Hunter Agent Endpoints
    # ─────────────────────────────────────────────────────────────────────────

    def test_lead_hunter_qualification(self):
        self.client.force_authenticate(user=self.user_a)

        prospect = Prospect.objects.create(
            business=self.biz_a,
            company_name="Innovate Ltd",
            contact_name="Alice Smith",
            industry="Technology",
            notes="Interested in bulk pricing."
        )

        score_url = reverse("lead_hunter:prospects-score", kwargs={
            "slug": self.biz_a.slug,
            "pk": str(prospect.id)
        })

        mock_payload = json.dumps({
            "score": 90,
            "tier": "hot",
            "summary": "Highly motivated tech buyer.",
            "next_action": "Send custom enterprise pricing sheet."
        })

        with patch("agents.lead_hunter.views.agent_chat", return_value=mock_payload) as mock_chat:
            resp = self.client.post(score_url)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            mock_chat.assert_called_once()
            prospect.refresh_from_db()
            self.assertEqual(prospect.score, 90)
            self.assertEqual(prospect.ai_summary, "Highly motivated tech buyer.")
