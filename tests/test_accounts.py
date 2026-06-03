from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice

User = get_user_model()

class SecurityEnhancementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='mfa@test.com',
            username='mfa@test.com',
            password='Password123!',
            first_name='MFA',
            last_name='User'
        )
        
    def test_totp_setup_requires_login(self):
        url = reverse('accounts:totp_setup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        
    def test_totp_challenge_intercepts_login(self):
        # Create a confirmed device
        TOTPDevice.objects.create(user=self.user, name='Phone', confirmed=True)
        
        # Try to login
        url = reverse('accounts:login')
        with self.settings(ALLOWED_HOSTS=['console.localhost', 'localhost', 'testserver']):
            response = self.client.post(url, {
                'username': 'mfa@test.com',
                'password': 'Password123!'
            }, HTTP_HOST='console.localhost:1234')
        
        # Should redirect to challenge, NOT to the dashboard
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:totp_challenge'))

        # Verify session has the totp_auth_user_id
        self.assertEqual(self.client.session.get('totp_auth_user_id'), self.user.id)
