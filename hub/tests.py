from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from hub.models import BusinessInstance

User = get_user_model()

class HubAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='testpassword'
        )
        self.business = BusinessInstance.objects.create(
            owner=self.user,
            name="Test Business",
            slug="test-biz",
            business_type="agency"
        )
        self.url = reverse('api:hub_api:business-list')

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_access_allowed(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Test Business")

    def test_jwt_token_obtain(self):
        url = reverse('api:token_obtain_pair')
        response = self.client.post(url, {'email': 'test@example.com', 'password': 'testpassword'}, format='json')
        # Assuming email backend or standard backend works here
        # If standard auth requires username instead:
        if response.status_code == 401:
            response = self.client.post(url, {'username': 'testuser', 'password': 'testpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

class AgentCatalogAPITests(APITestCase):
    def test_catalog_is_public(self):
        url = reverse('api:agents_global_api:catalog-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
