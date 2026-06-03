import json
import stripe
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
User = get_user_model()

from hub.models import BusinessInstance, BusinessSubscription, HubPlanConfig
from .models import BillingEvent, StripeCustomer

class StripeWebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test', password='password', email='test@test.com')
        self.business = BusinessInstance.objects.create(
            name='Test Business', 
            slug='test-bus', 
            owner=self.user,
            business_type='agency'
        )
        self.sub = BusinessSubscription.objects.create(
            business=self.business, 
            status='trial',
            stripe_subscription_id='sub_123'
        )
        # Create standard plan configuration
        HubPlanConfig.objects.get_or_create(
            plan_type='standard',
            display_name='Standard',
            monthly_price_usd=49.00,
            annual_price_usd=480.00
        )
        self.webhook_url = reverse('billing:webhook')

    def test_invalid_signature(self):
        response = self.client.post(self.webhook_url, data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    @patch('stripe.checkout.Session.create')
    @patch('stripe.Customer.create')
    def test_checkout_redirect(self, mock_customer_create, mock_session_create):
        # Mock Stripe calls
        mock_customer_create.return_value = MagicMock(id='cus_123')
        mock_session_create.return_value = MagicMock(url='https://checkout.stripe.com/pay/cs_123')

        # Log in the user using force_login to bypass django-axes
        self.client.force_login(self.user)

        url = reverse('billing:checkout', kwargs={'plan_type': 'standard'})
        response = self.client.get(f"{url}?cycle=monthly&business_id={self.business.id}")
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://checkout.stripe.com/pay/cs_123')

        # Verify StripeCustomer entry created
        stripe_cust = StripeCustomer.objects.filter(business=self.business).first()
        self.assertIsNotNone(stripe_cust)
        self.assertEqual(stripe_cust.stripe_customer_id, 'cus_123')

    @patch('stripe.billing_portal.Session.create')
    def test_portal_redirect(self, mock_portal_create):
        mock_portal_create.return_value = MagicMock(url='https://billing.stripe.com/portal/cs_123')
        
        # Link StripeCustomer
        StripeCustomer.objects.create(business=self.business, stripe_customer_id='cus_123')

        self.client.force_login(self.user)

        url = reverse('billing:portal')
        response = self.client.get(f"{url}?business_id={self.business.id}")
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://billing.stripe.com/portal/cs_123')

    @patch('stripe.Webhook.construct_event')
    @patch('stripe.Subscription.retrieve')
    def test_webhook_checkout_completed(self, mock_sub_retrieve, mock_construct_event):
        # Mock webhook verification using Stripe Event class constructs
        mock_event_dict = {
            'id': 'evt_123',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'customer': 'cus_123',
                    'subscription': 'sub_123',
                    'client_reference_id': str(self.business.id),
                    'metadata': {
                        'plan_type': 'standard',
                        'billing_cycle': 'monthly'
                    }
                }
            }
        }
        mock_event = stripe.Event.construct_from(mock_event_dict, stripe.api_key)
        mock_construct_event.return_value = mock_event

        # Mock stripe subscription retrieval (used to fetch active price ID)
        mock_sub = MagicMock()
        mock_sub.items.data = [MagicMock(price=MagicMock(id='price_999'))]
        mock_sub_retrieve.return_value = mock_sub

        response = self.client.post(
            self.webhook_url, 
            data=json.dumps(mock_event_dict), 
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        self.assertEqual(response.status_code, 200)

        # Refresh subscription and verify it's active standard plan
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.status, 'active')
        self.assertEqual(self.sub.plan_type, 'standard')
        self.assertEqual(self.sub.billing_cycle, 'monthly')
        self.assertEqual(self.sub.stripe_subscription_id, 'sub_123')
        self.assertEqual(self.sub.stripe_price_id, 'price_999')

        # Verify BillingEvent logged
        billing_event = BillingEvent.objects.filter(event_id='evt_123').first()
        self.assertIsNotNone(billing_event)
        self.assertEqual(billing_event.event_type, 'checkout.session.completed')

    @patch('stripe.Webhook.construct_event')
    def test_webhook_subscription_deleted(self, mock_construct_event):
        # Mock webhook subscription deleted
        mock_event_dict = {
            'id': 'evt_456',
            'type': 'customer.subscription.deleted',
            'data': {
                'object': {
                    'id': 'sub_123',
                    'customer': 'cus_123',
                    'status': 'canceled'
                }
            }
        }
        mock_event = stripe.Event.construct_from(mock_event_dict, stripe.api_key)
        mock_construct_event.return_value = mock_event

        response = self.client.post(
            self.webhook_url,
            data=json.dumps(mock_event_dict),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        self.assertEqual(response.status_code, 200)

        # Refresh subscription and verify status is updated to cancelled
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.status, 'cancelled')
