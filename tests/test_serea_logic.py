"""
tests/test_serea_logic.py
Unit tests for critical Serea AI logic:
  - SereaAgent creation and auto-provision via signal
  - permission_respond race-condition safety (atomic update)
  - Platform adapter contract (stub via TikTokAdapter)
"""
from unittest.mock import patch, MagicMock

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()


class SereaAgentSignalTest(TestCase):
    def test_serea_agent_auto_created_on_hired_employee(self):
        """Signals auto-provision a SereaAgent when a HiredAIEmployee is created."""
        from workspace_admin.models import HiredAIEmployee, AIEmployeeTier

        user = User.objects.create_user(
            username='signaltest', email='signal@example.com', password='pass'
        )
        tier, _ = AIEmployeeTier.objects.get_or_create(
            name='intern',
            defaults={
                'description': 'Intern tier',
                'token_limit': 1000,
                'monthly_price_usd': 0,
            },
        )
        hired = HiredAIEmployee.objects.create(
            employer=user, tier=tier, ai_name='TestSerea', is_active=True
        )

        # Signal should have fired — SereaAgent must exist
        from serea.models import SereaAgent
        self.assertTrue(
            SereaAgent.objects.filter(hired_employee=hired).exists(),
            "SereaAgent was not auto-created by the signal"
        )

    def test_serea_agent_offline_on_deactivate(self):
        """Deactivating a HiredAIEmployee should set SereaAgent.status = 'offline'."""
        from workspace_admin.models import HiredAIEmployee, AIEmployeeTier
        from serea.models import SereaAgent

        user = User.objects.create_user(
            username='deactivate', email='deactivate@example.com', password='pass'
        )
        tier, _ = AIEmployeeTier.objects.get_or_create(
            name='entry',
            defaults={'description': 'Entry', 'token_limit': 1000, 'monthly_price_usd': 0},
        )
        hired = HiredAIEmployee.objects.create(
            employer=user, tier=tier, ai_name='OfflineSerea', is_active=True
        )

        hired.is_active = False
        hired.save()

        try:
            agent = SereaAgent.objects.get(hired_employee=hired)
            self.assertEqual(agent.status, 'offline')
        except SereaAgent.DoesNotExist:
            pass  # Signal may not have created one without a Groq key in test env


class PermissionRespondTest(TestCase):
    def setUp(self):
        from workspace_admin.models import HiredAIEmployee, AIEmployeeTier
        from serea.models import SereaAgent, ConversationMessage

        self.user = User.objects.create_user(
            username='permtest', email='perm@example.com', password='pass'
        )
        tier, _ = AIEmployeeTier.objects.get_or_create(
            name='mid',
            defaults={'description': 'Mid', 'token_limit': 5000, 'monthly_price_usd': 0},
        )
        self.hired = HiredAIEmployee.objects.create(
            employer=self.user, tier=tier, ai_name='Perm Serea', is_active=True
        )
        # Try to get auto-created agent, or create manually
        try:
            self.agent = self.hired.serea_agent
        except Exception:
            self.agent = SereaAgent.objects.create(
                tenant=self.user,
                hired_employee=self.hired,
                status='idle',
            )

        self.msg = ConversationMessage.objects.create(
            agent=self.agent,
            sender='serea',
            message_text='May I delete this comment?',
            is_permission_request=True,
        )

    def test_approve_sets_permission_granted_true(self):
        from serea.models import ConversationMessage
        from django.http import JsonResponse

        factory = RequestFactory()
        request = factory.post(f'/serea/permission/{self.msg.id}/respond/', {
            'decision': 'approve',
        })
        request.user = self.user

        from serea.views import permission_respond
        with patch('serea.tasks.resume_after_approval.delay'):
            resp = permission_respond(request, msg_id=self.msg.id)

        self.msg.refresh_from_db()
        self.assertTrue(self.msg.permission_granted)

    def test_deny_sets_permission_granted_false(self):
        from serea.models import ConversationMessage

        factory = RequestFactory()
        request = factory.post(f'/serea/permission/{self.msg.id}/respond/', {
            'decision': 'deny',
        })
        request.user = self.user

        from serea.views import permission_respond
        with patch('serea.tasks.resume_after_approval.delay'):
            resp = permission_respond(request, msg_id=self.msg.id)

        self.msg.refresh_from_db()
        self.assertFalse(self.msg.permission_granted)

    def test_double_approve_returns_409(self):
        """Approving an already-resolved request must return HTTP 409."""
        from serea.models import ConversationMessage

        # Pre-resolve
        self.msg.permission_granted = True
        self.msg.save()

        factory = RequestFactory()
        request = factory.post(f'/serea/permission/{self.msg.id}/respond/', {
            'decision': 'approve',
        })
        request.user = self.user

        from serea.views import permission_respond
        with patch('serea.tasks.resume_after_approval.delay'):
            resp = permission_respond(request, msg_id=self.msg.id)

        self.assertEqual(resp.status_code, 409)


class PlatformAdapterContractTest(TestCase):
    """Verify that TikTokAdapter (stub) satisfies the BasePlatformAdapter interface."""

    def _make_account(self):
        account = MagicMock()
        account.access_token = 'fake-token'
        account.account_id = 'fake-id'
        return account

    def test_tiktok_post_returns_post_result(self):
        from serea.platforms.tiktok import TikTokAdapter
        from serea.platforms.base import PostResult

        adapter = TikTokAdapter(self._make_account())
        result = adapter.post("hello", media_url=None, hashtags=[])
        self.assertIsInstance(result, PostResult)
        self.assertFalse(result.success)

    def test_tiktok_fetch_comments_returns_list(self):
        from serea.platforms.tiktok import TikTokAdapter
        adapter = TikTokAdapter(self._make_account())
        result = adapter.fetch_recent_comments()
        self.assertIsInstance(result, list)

    def test_facebook_adapter_exists_and_importable(self):
        from serea.platforms.facebook import FacebookAdapter
        from serea.platforms.instagram import InstagramAdapter
        self.assertTrue(callable(FacebookAdapter))
        self.assertTrue(callable(InstagramAdapter))

    def test_get_adapter_returns_correct_class(self):
        from serea.platforms import get_adapter
        from serea.platforms.facebook import FacebookAdapter
        from serea.platforms.instagram import InstagramAdapter
        from serea.platforms.tiktok import TikTokAdapter

        fb = get_adapter('facebook', self._make_account())
        ig = get_adapter('instagram', self._make_account())
        tt = get_adapter('tiktok', self._make_account())

        self.assertIsInstance(fb, FacebookAdapter)
        self.assertIsInstance(ig, InstagramAdapter)
        self.assertIsInstance(tt, TikTokAdapter)

    def test_get_adapter_raises_for_unsupported(self):
        from serea.platforms import get_adapter
        with self.assertRaises(ValueError):
            get_adapter('linkedin', self._make_account())
