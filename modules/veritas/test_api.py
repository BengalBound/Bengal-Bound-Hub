from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import ClientApplication, ClientAgreement

User = get_user_model()

class VeritasAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='password123')
        
    def test_apply_kyb(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('veritas_api:apply-list')
        data = {
            'company_legal_name': 'Test Corp',
            'registration_number': '12345',
            'jurisdiction': 'US',
            'registered_address': '123 Main St',
            'business_type': 'Tech',
            'director_name': 'John Doe',
            'director_email': 'john@testcorp.com',
            'director_phone': '555-1234'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify application created
        app = ClientApplication.objects.get(user=self.user)
        self.assertEqual(app.company_legal_name, 'Test Corp')
        
        # Verify default agreements created
        agreements = ClientAgreement.objects.filter(application=app)
        self.assertEqual(agreements.count(), 4) # tos, dpa, aup, ai_ethics

    def test_inspector_gate(self):
        # Unapproved user should get 403 on agent API
        self.client.force_authenticate(user=self.user)
        # Create a pending application
        app = ClientApplication.objects.create(
            user=self.user, 
            company_legal_name='Test',
            status='submitted'
        )
        
        # Make a request to an agent API (mock endpoint)
        # We'll just test the middleware directly via the django test client
        client = Client()
        client.force_login(self.user)
        response = client.post('/api/agents/chat/', {}, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'KYB Verification Required', response.content)
        
        # Approve the application
        app.status = 'approved'
        app.save()
        
        # Now it should pass the veritas gate (though it might hit another 404/etc depending on the url)
        # The middleware itself shouldn't return 403 for KYB.
        response = client.post('/api/agents/chat/', {}, content_type='application/json')
        self.assertNotEqual(response.status_code, 403) # Actually it might be 403 from Compliance check, but not from KYB gate
