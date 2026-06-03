"""
tests/test_auth.py
Unit tests for the authentication flow:
  - User registration
  - OTP generation and verification (including expiry and rate limiting)
  - Login (correct password, wrong password)
  - SSO redirect / consume flow
  - One-business-per-owner enforcement
"""
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

    @patch('accounts.views.send_otp_email')
    def test_register_existing_unverified_user_resends_otp(self, mock_send):
        user = User.objects.create_user(username='unverified@example.com', email='unverified@example.com', password='pass')
        user.is_email_verified = False
        user.otp = '111111'
        user.save()

        resp = self.client.post(reverse('accounts:register'), {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'unverified@example.com',
            'password': 'TestPass1234!',
            'confirm_password': 'TestPass1234!',
            'business_name': 'Recover Business',
            'business_type': 'business',
            'installation_type': 'cloud',
        })
        
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/verify-otp/', resp.url)
        
        user.refresh_from_db()
        self.assertNotEqual(user.otp, '111111')
        self.assertFalse(user.is_email_verified)
        mock_send.assert_called_once()


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


class OTPResendTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='resenduser@example.com',
            email='resenduser@example.com',
            password='pass1234',
        )
        self.user.otp = '111111'
        self.user.save()

    @patch('accounts.views.send_otp_email')
    def test_resend_otp_regenerates_and_sends(self, mock_send):
        resp = self.client.get(reverse('accounts:resend_otp') + '?email=resenduser@example.com')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/verify-otp/', resp.url)

        self.user.refresh_from_db()
        self.assertNotEqual(self.user.otp, '111111')
        self.assertIsNotNone(self.user.otp)
        mock_send.assert_called_once_with(self.user, self.user.otp)


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
            'username': 'login@example.com',
            'password': 'correctpass',
        })
        self.assertIn(resp.status_code, [200, 302])
        self.assertTrue(resp.wsgi_request.user.is_authenticated)

    def test_wrong_password_does_not_log_in(self):
        resp = self.client.post(reverse('accounts:login'), {
            'username': 'login@example.com',
            'password': 'wrongpass',
        })
        # User should not be authenticated
        self.assertFalse(resp.wsgi_request.user.is_authenticated)

    @patch('accounts.views.send_otp_email')
    def test_login_redirects_unverified_user_to_otp(self, mock_send):
        unverified_user = User.objects.create_user(
            username='unverified_login@example.com',
            email='unverified_login@example.com',
            password='correctpass',
            is_email_verified=False,
        )
        
        from django.test import override_settings
        with override_settings(ACCOUNT_EMAIL_VERIFICATION='mandatory'):
            resp = self.client.post(reverse('accounts:login'), {
                'username': 'unverified_login@example.com',
                'password': 'correctpass',
            })
            
            self.assertEqual(resp.status_code, 302)
            self.assertIn('/accounts/verify-otp/', resp.url)
            
            unverified_user.refresh_from_db()
            self.assertIsNotNone(unverified_user.otp)
            mock_send.assert_called_once_with(unverified_user, unverified_user.otp)


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


class NextRedirectPreservationTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_allauth_signup_redirects_to_custom_register(self):
        # Visiting allauth signup page should redirect to custom register
        resp = self.client.get('/accounts/signup/?next=/foo/bar/')
        self.assertEqual(resp.status_code, 302)
        self.assertTrue('/accounts/register/' in resp.url)
        self.assertTrue('next=%2Ffoo%2Fbar%2F' in resp.url)

    @patch('accounts.views.send_otp_email')
    def test_registration_preserves_next_parameter(self, mock_send):
        # Registering with a next parameter should save it to session
        resp = self.client.post(reverse('accounts:register') + '?next=/target/url/', {
            'first_name': 'Preserve',
            'last_name': 'Redirect',
            'email': 'preserve@example.com',
            'password': 'TestPass1234!',
            'confirm_password': 'TestPass1234!',
            'business_name': 'Redirect Biz',
            'business_type': 'business',
            'installation_type': 'cloud',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/verify-otp/', resp.url)
        self.assertEqual(self.client.session.get('next'), '/target/url/')

        user = User.objects.get(email='preserve@example.com')
        otp = user.otp

        # Create allauth EmailAddress record
        from allauth.account.models import EmailAddress
        EmailAddress.objects.get_or_create(
            user=user,
            email=user.email,
            defaults={'primary': True, 'verified': False}
        )

        resp2 = self.client.post(reverse('accounts:verify_otp') + '?email=preserve@example.com', {'otp': otp})
        self.assertEqual(resp2.status_code, 200)
        self.assertContains(resp2, 'value="/target/url/"')

    def test_login_preserves_next_parameter(self):
        user = User.objects.create_user(
            username='login_preserve',
            email='login_preserve@example.com',
            password='correctpass',
            is_email_verified=True,
        )
        BusinessInstance.objects.create(
            owner=user,
            name='Login Target Biz',
            slug='target-biz',
            business_type='business',
        )

        resp = self.client.post(reverse('accounts:login') + '?next=/custom/dashboard/', {
            'username': 'login_preserve@example.com',
            'password': 'correctpass',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'value="/custom/dashboard/"')


class FirebaseAuthBridgeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.sync_url = reverse('accounts:firebase_sync')

    def test_sync_new_user_provisions_account_and_business(self):
        import jwt
        import json
        from hub.models import BusinessEmployee

        payload = {
            "uid": "fb_uid_123",
            "email": "new_fb_user@example.com",
            "name": "John Doe"
        }
        token = jwt.encode(payload, "a_very_secure_mock_token_secret_key_32_chars_long", algorithm="HS256")

        response = self.client.post(
            self.sync_url,
            data=json.dumps({"id_token": token}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertEqual(data["user"]["email"], "new_fb_user@example.com")
        self.assertEqual(data["user"]["firebase_uid"], "fb_uid_123")
        self.assertEqual(data["user"]["first_name"], "John")
        self.assertEqual(data["user"]["last_name"], "Doe")

        # Verify User created
        user = User.objects.filter(email="new_fb_user@example.com").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.firebase_uid, "fb_uid_123")
        self.assertTrue(user.is_email_verified)

        # Verify Business created and mapped to owner
        biz = BusinessInstance.objects.filter(owner=user).first()
        self.assertIsNotNone(biz)
        self.assertEqual(biz.name, "John's Company")

        # Verify BusinessEmployee created
        employee = BusinessEmployee.objects.filter(business=biz, user=user).first()
        self.assertIsNotNone(employee)
        self.assertEqual(employee.role, "owner")

    def test_sync_existing_user_by_email_updates_firebase_uid(self):
        import jwt
        import json

        existing_user = User.objects.create_user(
            email="existing_user@example.com",
            username="existing_user@example.com",
            password="SomePassword123!",
            is_email_verified=True,
            first_name="Jane",
            last_name="Smith"
        )
        self.assertIsNone(existing_user.firebase_uid)

        payload = {
            "uid": "fb_existing_uid",
            "email": "existing_user@example.com",
            "name": "Jane Smith"
        }
        token = jwt.encode(payload, "a_very_secure_mock_token_secret_key_32_chars_long", algorithm="HS256")

        response = self.client.post(
            self.sync_url,
            data=json.dumps({"id_token": token}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        
        existing_user.refresh_from_db()
        self.assertEqual(existing_user.firebase_uid, "fb_existing_uid")

    def test_sync_existing_user_by_uid_authenticates(self):
        import jwt
        import json

        user = User.objects.create_user(
            email="uid_match@example.com",
            username="uid_match@example.com",
            password="SomePassword123!",
            is_email_verified=True,
            firebase_uid="fb_uid_match"
        )

        payload = {
            "uid": "fb_uid_match",
            "email": "another_email@example.com"
        }
        token = jwt.encode(payload, "a_very_secure_mock_token_secret_key_32_chars_long", algorithm="HS256")

        response = self.client.post(
            self.sync_url,
            data=json.dumps({"id_token": token}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user"]["email"], "uid_match@example.com")

    def test_sync_missing_token_or_invalid_claims(self):
        import jwt
        import json

        # Missing token
        response = self.client.post(self.sync_url, data=json.dumps({}), content_type="application/json")
        self.assertEqual(response.status_code, 400)

        # Missing email/uid
        token = jwt.encode({"name": "No Info User"}, "a_very_secure_mock_token_secret_key_32_chars_long", algorithm="HS256")
        response = self.client.post(self.sync_url, data=json.dumps({"id_token": token}), content_type="application/json")
        self.assertEqual(response.status_code, 400)

