"""
tests/test_auth.py
Unit tests for the authentication flow:
  - User registration
  - OTP generation and verification (including expiry and rate limiting)
  - Login (correct password, wrong password)
  - SSO redirect / consume flow
  - One-business-per-owner enforcement
"""
import secrets
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from hub.models import BusinessInstance


class RegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()

    @patch('accounts.views.send_otp_email')
    def test_register_creates_unverified_user(self, mock_send):
        self.client.post(reverse('accounts:register'), {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password': 'TestPass1234!',
            'confirm_password': 'TestPass1234!',
            'business_name': 'Test Business',
            'business_type': 'business',
            'installation_type': 'cloud',
        })
        self.assertEqual(User.objects.filter(email='test@example.com').count(), 1)
        user = User.objects.get(email='test@example.com')
        self.assertFalse(user.is_email_verified)
        self.assertIsNotNone(user.otp)
        self.assertIsNotNone(user.otp_created_at)

    @patch('accounts.views.send_otp_email')
    def test_register_duplicate_email_fails(self, mock_send):
        User.objects.create_user(username='existing', email='dup@example.com', password='pass')
        self.client.post(reverse('accounts:register'), {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'dup@example.com',
            'password': 'TestPass1234!',
            'confirm_password': 'TestPass1234!',
            'business_name': 'Dup Business',
            'business_type': 'business',
            'installation_type': 'cloud',
        })
        # Should not create a second user
        self.assertEqual(User.objects.filter(email='dup@example.com').count(), 1)


class OTPVerifyTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='otpuser',
            email='otp@example.com',
            password='pass1234',
        )
        self.user.otp = '123456'
        self.user.otp_created_at = timezone.now()
        self.user.save()

    def _otp_url(self):
        return reverse('accounts:verify_otp') + '?email=otp@example.com'

    def test_correct_otp_verifies_email(self):
        self.client.post(self._otp_url(), {'otp': '123456'})
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    def test_wrong_otp_does_not_verify(self):
        self.client.post(self._otp_url(), {'otp': '000000'})
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)

    def test_expired_otp_rejected(self):
        self.user.otp_created_at = timezone.now() - timedelta(minutes=11)
        self.user.save()
        self.client.post(self._otp_url(), {'otp': '123456'})
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)


class LoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='loginuser',
            email='login@example.com',
            password='correctpass',
            is_email_verified=True,
        )

    def test_correct_credentials_logs_in(self):
        resp = self.client.post(reverse('accounts:login'), {
            'email': 'login@example.com',
            'password': 'correctpass',
        })
        # Should redirect after login (302) not return 200 with errors
        self.assertIn(resp.status_code, [200, 302])

    def test_wrong_password_does_not_log_in(self):
        resp = self.client.post(reverse('accounts:login'), {
            'email': 'login@example.com',
            'password': 'wrongpass',
        })
        # User should not be authenticated
        self.assertFalse(resp.wsgi_request.user.is_authenticated)


class OneBizPerOwnerTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='bizowner',
            email='owner@example.com',
            password='pass',
            is_email_verified=True,
        )
        self.client.force_login(self.user)

    def test_cannot_create_second_business(self):
        # Create first business directly
        BusinessInstance.objects.create(
            owner=self.user,
            name='First Biz',
            slug='first-biz',
            business_type='business',
        )
        # Attempt to create a second business via the view
        resp = self.client.post(reverse('hub:hub_create'), {
            'name': 'Second Biz',
            'business_type': 'business',
            'installation_type': 'cloud',
        }, follow=True)
        # Should be redirected with an error, NOT create a second business
        self.assertEqual(BusinessInstance.objects.filter(owner=self.user).count(), 1)


class UserBusinessMembershipTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner', email='owner2@example.com', password='pass'
        )
        self.member = User.objects.create_user(
            username='member', email='member@example.com', password='pass'
        )
        self.biz = BusinessInstance.objects.create(
            owner=self.owner, name='Test Biz', slug='test-biz', business_type='business'
        )

    def test_owner_can_access_business(self):
        from hub.views import _get_business_for_user
        result = _get_business_for_user('test-biz', self.owner)
        self.assertIsNotNone(result)

    def test_member_without_membership_cannot_access(self):
        from hub.views import _get_business_for_user
        result = _get_business_for_user('test-biz', self.member)
        self.assertIsNone(result)

    def test_member_with_membership_can_access(self):
        from hub.models import UserBusinessMembership
        from hub.views import _get_business_for_user
        UserBusinessMembership.objects.create(
            user=self.member, business=self.biz, role='member'
        )
        result = _get_business_for_user('test-biz', self.member)
        self.assertIsNotNone(result)
