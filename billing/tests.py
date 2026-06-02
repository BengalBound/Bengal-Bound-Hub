import json
from django.test import TestCase, Client
from django.urls import reverse
from hub.models import BusinessInstance, BusinessSubscription
from django.contrib.auth.models import User
from .models import BillingEvent, StripeCustomer

class StripeWebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test', email='test@test.com')
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
        self.url = reverse('billing:webhook')

    def test_invalid_signature(self):
        response = self.client.post(self.url, data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    # In a full test suite, we would use unittest.mock to patch stripe.Webhook.construct_event
    # and pass in realistic JSON payload events to verify BusinessSubscription status changes.
