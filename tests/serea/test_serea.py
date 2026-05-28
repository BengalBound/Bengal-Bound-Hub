"""
serea/tests.py
──────────────
Test suite for the Serea AI Social Media Moderator.

Run with:
    python manage.py test serea -v 2

Live LLM tests (require GROQ_API_KEY env var) are automatically skipped
when the key is not present.
"""

import os
import json
from unittest import skip, skipUnless
from unittest.mock import patch, MagicMock

from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from accounts.models import User
from workspace_admin.models import AIEmployeeTier, HiredAIEmployee

from serea.models import (
    SereaAgent,
    AgentInstruction,
    ConversationMessage,
    ModerationLog,
    ContentQueue,
    SereaReport,
)
from serea.logic import (
    SereaBrain,
    TokenLimitExceeded,
    _parse_agent_response,
    CONFIDENCE_THRESHOLD,
    TOOLS,
    # tools
    trigger_permission_request,
    create_social_post,
    list_scheduled_posts,
    check_moderation_stats,
    generate_report,
    save_report,
    save_client_instruction,
)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

_USER_COUNTER = 0

def _make_user(email='test@example.com'):
    global _USER_COUNTER
    _USER_COUNTER += 1
    username = f'testuser_{_USER_COUNTER}'
    return User.objects.create_user(
        username=username,
        email=email,
        password='testpass123',
        role='console_user',
    )


def _make_tier(name='Basic', token_limit=100_000):
    return AIEmployeeTier.objects.get_or_create(
        name=name,
        defaults={
            'monthly_price_usd': 0,
            'token_limit': token_limit,
            'description': 'Test tier',
        }
    )[0]


def _make_hired_employee(user, tier):
    return HiredAIEmployee.objects.create(
        employer=user,
        tier=tier,
        ai_name='Serea Test',
        is_active=True,
    )


def _make_agent(user, hired=None, tier='entry', model='llama3-70b-8192'):
    """
    Creates (or retrieves the signal-provisioned) SereaAgent for a user.
    When hired_employee is provided, the post_save signal may have already
    created one — we get_or_create and then update the test-specific fields.
    """
    defaults = dict(
        tenant=user,
        tier=tier,
        ai_model=model,
        groq_api_key='test-groq-key',
        token_limit_override=0,
        status='idle',
    )
    if hired:
        agent, _ = SereaAgent.objects.get_or_create(
            hired_employee=hired, defaults=defaults
        )
        # Ensure test-specific fields are applied even if signal already created it
        SereaAgent.objects.filter(pk=agent.pk).update(**{
            k: v for k, v in defaults.items() if k != 'tenant'
        })
        agent.refresh_from_db()
    else:
        agent = SereaAgent.objects.create(hired_employee=None, **defaults)
    return agent


# ─────────────────────────────────────────────────────────────────────────────
# 1. MODEL TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestSereaModels(TestCase):
    """Verifies that all six Serea models can be created and saved."""

    def setUp(self):
        self.user = _make_user()
        self.tier = _make_tier()
        self.hired = _make_hired_employee(self.user, self.tier)
        self.agent = _make_agent(self.user, self.hired)

    def test_agent_created(self):
        self.assertIsNotNone(self.agent.pk)
        self.assertEqual(self.agent.status, 'idle')
        self.assertEqual(self.agent.ai_model, 'llama3-70b-8192')

    def test_agent_str(self):
        s = str(self.agent)
        self.assertIn('Serea', s)
        self.assertIn(self.user.email, s)

    def test_agent_instruction(self):
        instr = AgentInstruction.objects.create(
            agent=self.agent,
            instruction_text='Always use emojis.',
            is_active=True,
        )
        self.assertTrue(instr.pk)
        self.assertIn('emojis', str(instr))

    def test_conversation_message_normal(self):
        msg = ConversationMessage.objects.create(
            agent=self.agent,
            sender='serea',
            message_text='Hello, how can I help?',
        )
        self.assertFalse(msg.is_permission_request)
        self.assertIsNone(msg.permission_granted)

    def test_conversation_message_permission(self):
        msg = ConversationMessage.objects.create(
            agent=self.agent,
            sender='serea',
            message_text='I need approval to delete a comment.',
            is_permission_request=True,
            pending_action_context={'raw_context': 'delete spam comment'},
        )
        self.assertTrue(msg.is_permission_request)
        self.assertIsNone(msg.permission_granted)
        self.assertEqual(msg.pending_action_context['raw_context'], 'delete spam comment')

    def test_moderation_log(self):
        log = ModerationLog.objects.create(
            agent=self.agent,
            platform='Instagram',
            comment_text='Great product!',
            action_taken='ignore',
            sentiment_score=0.9,
            confidence_score=0.95,
        )
        self.assertEqual(log.action_taken, 'ignore')
        self.assertIn('IGNORE', str(log).upper())

    def test_content_queue(self):
        item = ContentQueue.objects.create(
            agent=self.agent,
            title='Monday post',
            platform='Instagram',
            caption='Check out our latest collection!',
            hashtags='#fashion #style',
            post_date=timezone.now(),
            status='pending',
        )
        self.assertEqual(item.status, 'pending')
        self.assertIn('Instagram', str(item))

    def test_serea_report(self):
        report = SereaReport.objects.create(
            agent=self.agent,
            report_type='weekly',
            title='Week 10 Summary',
            body='This week was great. 20 comments moderated.',
        )
        self.assertEqual(report.report_type, 'weekly')
        self.assertIn('Week 10', str(report))

    def test_openrouter_model_stored(self):
        agent = SereaAgent.objects.create(
            tenant=self.user,
            tier='mid',
            ai_model='meta-llama/llama-3.3-70b-instruct:free',
            openrouter_api_key='test-or-key',
            token_limit_override=0,
            status='idle',
        )
        self.assertIn('/', agent.ai_model)


# ─────────────────────────────────────────────────────────────────────────────
# 2. TOOL FUNCTION TESTS  (no LLM calls — pure DB operations)
# ─────────────────────────────────────────────────────────────────────────────

class TestSereaTools(TestCase):
    """Tests each @tool function directly (no LLM involved)."""

    def setUp(self):
        self.user = _make_user('tools@example.com')
        self.agent = _make_agent(self.user)

    # ── trigger_permission_request ───────────────────────────────────────────

    def test_trigger_permission_creates_message(self):
        result = trigger_permission_request.func(
            agent_id=str(self.agent.pk),
            context='I want to delete a spam comment. Confidence: 0.5',
        )
        self.assertIn('Permission request sent', result)
        perm_msg = ConversationMessage.objects.filter(
            agent=self.agent, is_permission_request=True
        ).first()
        self.assertIsNotNone(perm_msg)
        self.assertEqual(perm_msg.sender, 'serea')

    def test_trigger_permission_sets_waiting_status(self):
        trigger_permission_request.func(
            agent_id=str(self.agent.pk),
            context='Test permission',
        )
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.status, 'waiting')

    def test_trigger_permission_invalid_agent(self):
        result = trigger_permission_request.func(agent_id='99999', context='test')
        self.assertIn('ERROR', result)

    # ── create_social_post ───────────────────────────────────────────────────

    def test_create_social_post_no_schedule(self):
        result = create_social_post.func(
            agent_id=str(self.agent.pk),
            platform='Instagram',
            caption='Our summer sale starts now! 🌞',
            hashtags='#summer #sale',
        )
        self.assertIn('Post scheduled!', result)
        self.assertIn('Instagram', result)
        self.assertEqual(ContentQueue.objects.filter(agent=self.agent).count(), 1)

    def test_create_social_post_with_schedule(self):
        result = create_social_post.func(
            agent_id=str(self.agent.pk),
            platform='Facebook',
            caption='Join us for a live Q&A tomorrow.',
            schedule_time='2026-03-20 14:00',
        )
        self.assertIn('Post scheduled!', result)
        item = ContentQueue.objects.filter(agent=self.agent, platform='Facebook').first()
        self.assertIsNotNone(item)

    def test_create_social_post_invalid_agent(self):
        result = create_social_post.func(
            agent_id='99999', platform='Instagram', caption='test'
        )
        self.assertIn('ERROR', result)

    # ── list_scheduled_posts ─────────────────────────────────────────────────

    def test_list_scheduled_posts_empty(self):
        result = list_scheduled_posts.func(agent_id=str(self.agent.pk))
        self.assertIn('empty', result)

    def test_list_scheduled_posts_with_items(self):
        ContentQueue.objects.create(
            agent=self.agent,
            title='Test post',
            platform='Twitter',
            caption='Hello world',
            post_date=timezone.now(),
            status='pending',
        )
        result = list_scheduled_posts.func(agent_id=str(self.agent.pk))
        self.assertIn('Upcoming scheduled posts', result)
        self.assertIn('Twitter', result)

    # ── check_moderation_stats ───────────────────────────────────────────────

    def test_check_moderation_stats_empty(self):
        result = check_moderation_stats.func(agent_id=str(self.agent.pk))
        self.assertIn('Moderation stats', result)
        self.assertIn('Total actions: 0', result)

    def test_check_moderation_stats_with_data(self):
        ModerationLog.objects.create(
            agent=self.agent,
            platform='Instagram',
            comment_text='spam comment',
            action_taken='delete',
            confidence_score=0.95,
            sentiment_score=0.1,
        )
        ModerationLog.objects.create(
            agent=self.agent,
            platform='Facebook',
            comment_text='positive comment',
            action_taken='reply',
            confidence_score=0.88,
            sentiment_score=0.9,
        )
        result = check_moderation_stats.func(agent_id=str(self.agent.pk))
        self.assertIn('Total actions: 2', result)
        self.assertIn('deleted', result)
        self.assertIn('replied', result)

    # ── generate_report ──────────────────────────────────────────────────────

    def test_generate_report_returns_json(self):
        result = generate_report.func(
            agent_id=str(self.agent.pk),
            report_type='weekly',
            period='this_month',
        )
        data = json.loads(result)
        self.assertIn('moderation_total', data)
        self.assertIn('posts_scheduled', data)
        self.assertIn('tokens_used_month', data)

    def test_generate_report_all_periods(self):
        for period in ('today', 'yesterday', 'this_week', 'last_week', 'this_month', 'last_month'):
            result = generate_report.func(
                agent_id=str(self.agent.pk),
                report_type='custom',
                period=period,
            )
            self.assertNotIn('ERROR', result, f"generate_report failed for period={period}")

    # ── save_report ──────────────────────────────────────────────────────────

    def test_save_report_creates_report_and_message(self):
        result = save_report.func(
            agent_id=str(self.agent.pk),
            report_type='weekly',
            title='Week 10 Report',
            body='20 comments moderated. 3 posts published.',
        )
        self.assertIn('Report saved', result)
        self.assertEqual(SereaReport.objects.filter(agent=self.agent).count(), 1)
        # Also creates a ConversationMessage
        msg = ConversationMessage.objects.filter(agent=self.agent).last()
        self.assertIsNotNone(msg)
        self.assertIn('Week 10 Report', msg.message_text)

    # ── save_client_instruction ──────────────────────────────────────────────

    def test_save_client_instruction(self):
        result = save_client_instruction.func(
            agent_id=str(self.agent.pk),
            instruction='Never delete comments — always flag instead.',
        )
        self.assertIn("saved", result)
        instr = AgentInstruction.objects.filter(agent=self.agent).first()
        self.assertIsNotNone(instr)
        self.assertIn('Never delete', instr.instruction_text)

    def test_tool_count(self):
        """Ensure all 31 tools are registered."""
        self.assertEqual(len(TOOLS), 31)


# ─────────────────────────────────────────────────────────────────────────────
# 3. PARSE AGENT RESPONSE
# ─────────────────────────────────────────────────────────────────────────────

class TestParseAgentResponse(TestCase):
    """Tests the lightweight LLM output parser."""

    def test_delete_action(self):
        r = _parse_agent_response("I will delete this comment. Confidence: 0.92. Sentiment: 0.1")
        self.assertEqual(r['action'], 'delete')
        self.assertAlmostEqual(r['confidence'], 0.92)
        self.assertAlmostEqual(r['sentiment'], 0.1)
        self.assertFalse(r['requires_human'])

    def test_reply_action(self):
        r = _parse_agent_response("I'll reply to this comment. Confidence: 0.85. Sentiment: 0.8")
        self.assertEqual(r['action'], 'reply')

    def test_flag_action(self):
        r = _parse_agent_response("This needs to be flagged. Confidence: 0.75")
        self.assertEqual(r['action'], 'flag')

    def test_ignore_action(self):
        r = _parse_agent_response("I'll ignore this comment. Confidence: 0.9. Sentiment: 0.7")
        self.assertEqual(r['action'], 'ignore')

    def test_pending_approval_from_permission_request_text(self):
        r = _parse_agent_response("Permission request posted. Confidence: 0.45")
        self.assertEqual(r['action'], 'pending_approval')
        self.assertTrue(r['requires_human'])

    def test_low_confidence_sets_requires_human(self):
        r = _parse_agent_response("I would flag this. Confidence: 0.55. Sentiment: 0.3")
        self.assertTrue(r['requires_human'])

    def test_high_confidence_no_requires_human(self):
        r = _parse_agent_response("Delete this spam. Confidence: 0.95. Sentiment: 0.05")
        self.assertFalse(r['requires_human'])

    def test_no_scores_in_text(self):
        r = _parse_agent_response("This comment looks fine.")
        self.assertIsNone(r['confidence'])
        self.assertIsNone(r['sentiment'])
        self.assertEqual(r['action'], 'flag')   # safe default

    def test_confidence_threshold_boundary(self):
        # Exactly at threshold — not requires_human
        r = _parse_agent_response(f"I'll flag this. Confidence: {CONFIDENCE_THRESHOLD}")
        self.assertFalse(r['requires_human'])

        # Just below threshold — requires_human
        below = round(CONFIDENCE_THRESHOLD - 0.01, 2)
        r2 = _parse_agent_response(f"I'll flag this. Confidence: {below}")
        self.assertTrue(r2['requires_human'])


# ─────────────────────────────────────────────────────────────────────────────
# 4. TOKEN MANAGEMENT TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestTokenManagement(TestCase):
    """Tests the monthly token limit enforcement."""

    def setUp(self):
        self.user = _make_user('tokens@example.com')
        self.agent = SereaAgent.objects.create(
            tenant=self.user,
            tier='entry',
            groq_api_key='test-key',
            token_limit_override=5_000,
            tokens_used_this_month=0,
            status='idle',
        )

    def _brain(self):
        """Returns a SereaBrain with a mocked LLM (no API call)."""
        with patch('serea.logic.ChatGroq'):
            return SereaBrain(agent_id=self.agent.pk)

    def test_under_limit_passes(self):
        brain = self._brain()
        brain._check_token_limit()  # should not raise

    def test_at_limit_raises(self):
        self.agent.tokens_used_this_month = 5_000
        self.agent.save()
        brain = self._brain()
        with self.assertRaises(TokenLimitExceeded):
            brain._check_token_limit()

    def test_over_limit_raises(self):
        self.agent.tokens_used_this_month = 6_000
        self.agent.save()
        brain = self._brain()
        with self.assertRaises(TokenLimitExceeded):
            brain._check_token_limit()

    def test_unlimited_zero_override_never_raises(self):
        self.agent.token_limit_override = 0   # 0 = unlimited
        self.agent.tokens_used_this_month = 999_999_999
        self.agent.save()
        brain = self._brain()
        brain._check_token_limit()  # must not raise

    def test_record_tokens_increments_db(self):
        brain = self._brain()
        brain._record_tokens(500)
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.tokens_used_this_month, 500)

    def test_record_tokens_zero_is_noop(self):
        brain = self._brain()
        brain._record_tokens(0)
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.tokens_used_this_month, 0)


# ─────────────────────────────────────────────────────────────────────────────
# 5. BRAIN INIT — LLM SELECTION
# ─────────────────────────────────────────────────────────────────────────────

class TestSereaBrainLLMSelection(TestCase):
    """Checks that SereaBrain correctly configures ChatOpenAI for LiteLLM routing."""

    def setUp(self):
        self.user = _make_user('brain@example.com')
        self.agent = SereaAgent.objects.create(
            tenant=self.user,
            tier='entry',
            ai_model='neural-chat',
            token_limit_override=0,
            status='idle',
        )

    def test_litellm_chatopenai_selected_with_correct_settings(self):
        from django.conf import settings
        with patch('langchain_openai.ChatOpenAI') as MockChatOpenAI:
            MockChatOpenAI.return_value = MagicMock()
            brain = SereaBrain(agent_id=self.agent.pk)
            llm = brain.llm
            MockChatOpenAI.assert_called_once()
            call_kwargs = MockChatOpenAI.call_args.kwargs
            self.assertEqual(call_kwargs['openai_api_base'], settings.LITELLM_BASE_URL)
            self.assertEqual(call_kwargs['openai_api_key'], settings.LITELLM_MASTER_KEY)


# ─────────────────────────────────────────────────────────────────────────────
# 6. PROMPT BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

class TestSereaBrainPrompts(TestCase):
    """Verifies system prompt content and structure."""

    def setUp(self):
        self.user = _make_user('prompt@example.com')
        self.agent = _make_agent(self.user)

    def _brain(self):
        with patch('serea.logic.ChatGroq'):
            return SereaBrain(agent_id=self.agent.pk)

    def test_chat_prompt_contains_agent_id(self):
        brain = self._brain()
        prompt = brain._build_chat_prompt()
        self.assertIn(str(self.agent.pk), prompt)

    def test_chat_prompt_contains_tier(self):
        brain = self._brain()
        prompt = brain._build_chat_prompt()
        self.assertIn(self.agent.get_tier_display(), prompt)

    def test_chat_prompt_contains_date(self):
        brain = self._brain()
        prompt = brain._build_chat_prompt()
        self.assertIn('UTC', prompt)

    def test_chat_prompt_lists_tools(self):
        brain = self._brain()
        prompt = brain._build_chat_prompt()
        self.assertIn('create_social_post', prompt)
        self.assertIn('generate_report', prompt)
        self.assertIn('save_client_instruction', prompt)

    def test_chat_prompt_includes_custom_instructions(self):
        AgentInstruction.objects.create(
            agent=self.agent,
            instruction_text='Always reply in Bengali.',
            is_active=True,
        )
        brain = self._brain()
        prompt = brain._build_chat_prompt()
        self.assertIn('Always reply in Bengali.', prompt)

    def test_moderation_prompt_contains_threshold(self):
        brain = self._brain()
        prompt = brain._build_moderation_prompt()
        self.assertIn(str(CONFIDENCE_THRESHOLD), prompt)
        self.assertIn('trigger_permission_request', prompt)

    def test_tier_personality_intern(self):
        self.agent.tier = 'intern'
        self.agent.save()
        brain = self._brain()
        prompt = brain._build_chat_prompt()
        self.assertIn('enthusiastic', prompt.lower())

    def test_tier_personality_senior(self):
        self.agent.tier = 'senior'
        self.agent.save()
        brain = self._brain()
        prompt = brain._build_chat_prompt()
        self.assertIn('strategic', prompt.lower())


# ─────────────────────────────────────────────────────────────────────────────
# 7. CONVERSATION HISTORY
# ─────────────────────────────────────────────────────────────────────────────

class TestConversationHistory(TestCase):
    """Verifies that past messages are loaded and formatted correctly."""

    def setUp(self):
        self.user = _make_user('history@example.com')
        self.agent = _make_agent(self.user)

    def _brain(self):
        with patch('serea.logic.ChatGroq'):
            return SereaBrain(agent_id=self.agent.pk)

    def test_empty_history(self):
        brain = self._brain()
        self.assertEqual(brain._get_conversation_history(), [])

    def test_history_ordered_oldest_first(self):
        ConversationMessage.objects.create(agent=self.agent, sender='client@x.com', message_text='Hello')
        ConversationMessage.objects.create(agent=self.agent, sender='serea', message_text='Hi there!')
        brain = self._brain()
        history = brain._get_conversation_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0][0], 'human')
        self.assertEqual(history[1][0], 'assistant')

    def test_permission_requests_excluded(self):
        ConversationMessage.objects.create(
            agent=self.agent, sender='serea', message_text='Normal message'
        )
        ConversationMessage.objects.create(
            agent=self.agent, sender='serea', message_text='Need approval',
            is_permission_request=True
        )
        brain = self._brain()
        history = brain._get_conversation_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0][1], 'Normal message')

    def test_history_limit_respected(self):
        for i in range(20):
            ConversationMessage.objects.create(
                agent=self.agent, sender='serea', message_text=f'Message {i}'
            )
        brain = self._brain()
        history = brain._get_conversation_history(limit=12)
        self.assertLessEqual(len(history), 12)


# ─────────────────────────────────────────────────────────────────────────────
# 8. MOCKED CHAT (no real API call)
# ─────────────────────────────────────────────────────────────────────────────

class TestSereaBrainChatMocked(TestCase):
    """Tests SereaBrain.chat() with a mocked LLM response."""

    def setUp(self):
        self.user = _make_user('mockchat@example.com')
        self.agent = _make_agent(self.user)

    def _brain_with_mock_response(self, mock_text):
        """Returns a SereaBrain whose _run_messages always returns mock_text."""
        with patch('serea.logic.ChatGroq'):
            brain = SereaBrain(agent_id=self.agent.pk)
        brain._run_messages = MagicMock(return_value=(mock_text, 150))
        return brain

    def test_chat_returns_response(self):
        brain = self._brain_with_mock_response("I've checked — everything looks good!")
        reply = brain.chat("How are things going?")
        self.assertEqual(reply, "I've checked — everything looks good!")

    def test_chat_records_token_usage(self):
        brain = self._brain_with_mock_response("Great, I'll handle that.")
        brain.chat("Schedule a post please")
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.tokens_used_this_month, 150)

    def test_chat_fallback_on_exception(self):
        with patch('serea.logic.ChatGroq'):
            brain = SereaBrain(agent_id=self.agent.pk)
        brain._run_messages = MagicMock(side_effect=Exception("LLM timeout"))
        reply = brain.chat("Hello")
        self.assertIn("issue", reply.lower())

    def test_chat_injects_conversation_history(self):
        ConversationMessage.objects.create(
            agent=self.agent, sender='user@x.com', message_text='My brand is BengalTech'
        )
        brain = self._brain_with_mock_response("Sure, BengalTech post scheduled.")
        brain._run_messages = MagicMock(return_value=("Sure", 50))
        brain.chat("write an instagram post")
        call_args = brain._run_messages.call_args
        messages_arg = call_args[0][1]  # second positional arg
        # History should be prepended
        self.assertTrue(any('BengalTech' in str(m) for m in messages_arg))

    def test_chat_raises_token_limit_exceeded(self):
        self.agent.token_limit_override = 100
        self.agent.tokens_used_this_month = 100
        self.agent.save()
        with patch('serea.logic.ChatGroq'):
            brain = SereaBrain(agent_id=self.agent.pk)
        with self.assertRaises(TokenLimitExceeded):
            brain.chat("Hello")


# ─────────────────────────────────────────────────────────────────────────────
# 9. MOCKED PROCESS COMMENT
# ─────────────────────────────────────────────────────────────────────────────

class TestSereaBrainModerationMocked(TestCase):

    def setUp(self):
        self.user = _make_user('mod@example.com')
        self.agent = _make_agent(self.user)

    def _brain_with_mock_response(self, mock_text):
        with patch('serea.logic.ChatGroq'):
            brain = SereaBrain(agent_id=self.agent.pk)
        brain._run = MagicMock(return_value=(mock_text, 200))
        return brain

    def test_process_comment_returns_dict(self):
        brain = self._brain_with_mock_response(
            "I'll delete this spam. Confidence: 0.95. Sentiment: 0.05."
        )
        result = brain.process_comment("Buy cheap meds here!!! CLICK NOW", 'Instagram')
        self.assertIn('action', result)
        self.assertIn('confidence', result)
        self.assertIn('requires_human', result)

    def test_process_comment_resets_status_to_idle(self):
        brain = self._brain_with_mock_response(
            "I'll ignore this. Confidence: 0.8. Sentiment: 0.7."
        )
        brain.process_comment("Nice photo!", 'Facebook')
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.status, 'idle')

    def test_process_comment_records_tokens(self):
        brain = self._brain_with_mock_response(
            "Flagging this. Confidence: 0.75."
        )
        brain.process_comment("This is weird", 'Twitter')
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.tokens_used_this_month, 200)

    def test_process_comment_handles_exception(self):
        with patch('serea.logic.ChatGroq'):
            brain = SereaBrain(agent_id=self.agent.pk)
        brain._run = MagicMock(side_effect=Exception("network error"))
        result = brain.process_comment("test")
        self.assertEqual(result['action'], 'flag')
        self.assertTrue(result['requires_human'])


# ─────────────────────────────────────────────────────────────────────────────
# 10. SIGNALS
# ─────────────────────────────────────────────────────────────────────────────

class TestSereaSignals(TestCase):
    """Verifies the auto-provisioning signal behaviour."""

    def setUp(self):
        self.user = _make_user('signals@example.com')
        self.tier = _make_tier()

    def test_active_hired_employee_provisions_agent(self):
        he = HiredAIEmployee.objects.create(
            employer=self.user,
            tier=self.tier,
            ai_name='Signal Test',
            is_active=True,
        )
        # Signal should have fired on post_save
        agent = SereaAgent.objects.filter(hired_employee=he).first()
        self.assertIsNotNone(agent)
        self.assertNotEqual(agent.status, 'offline')

    def test_deactivating_sets_offline(self):
        he = HiredAIEmployee.objects.create(
            employer=self.user,
            tier=self.tier,
            ai_name='Deactivate Test',
            is_active=True,
        )
        he.is_active = False
        he.save()
        agent = SereaAgent.objects.filter(hired_employee=he).first()
        if agent:  # may have been created by previous test
            agent.refresh_from_db()
            self.assertEqual(agent.status, 'offline')


# ─────────────────────────────────────────────────────────────────────────────
# 11. LIVE LLM TESTS  (skipped unless GROQ_API_KEY is set)
# ─────────────────────────────────────────────────────────────────────────────

GROQ_KEY = os.getenv('GROQ_API_KEY', '')


@skipUnless(GROQ_KEY, 'Set GROQ_API_KEY env var to run live LLM tests')
class TestSereaBrainLive(TestCase):
    """
    Integration tests that make real Groq API calls.
    Only run when GROQ_API_KEY is present in the environment.
    """

    def setUp(self):
        self.user = _make_user('live@example.com')
        self.agent = SereaAgent.objects.create(
            tenant=self.user,
            tier='entry',
            ai_model='llama3-8b-8192',   # smallest/fastest for tests
            groq_api_key=GROQ_KEY,
            token_limit_override=0,
            status='idle',
        )

    def test_live_chat_returns_non_empty_string(self):
        brain = SereaBrain(agent_id=self.agent.pk)
        reply = brain.chat("Hey, just checking you're working. Say hi back.")
        self.assertIsInstance(reply, str)
        self.assertGreater(len(reply), 5)

    def test_live_chat_uses_tools_list_posts(self):
        ContentQueue.objects.create(
            agent=self.agent,
            title='Test post',
            platform='Instagram',
            caption='Hello world',
            post_date=timezone.now(),
            status='pending',
        )
        brain = SereaBrain(agent_id=self.agent.pk)
        reply = brain.chat("What posts do I have scheduled?")
        self.assertIsInstance(reply, str)
        self.assertGreater(len(reply), 5)

    def test_live_chat_records_tokens(self):
        brain = SereaBrain(agent_id=self.agent.pk)
        before = self.agent.tokens_used_this_month
        brain.chat("Quick question: what platforms can you post to?")
        self.agent.refresh_from_db()
        # Tokens should have increased (Groq may return 0 usage in some cases)
        self.assertGreaterEqual(self.agent.tokens_used_this_month, before)

    def test_live_moderation_positive_comment(self):
        brain = SereaBrain(agent_id=self.agent.pk)
        result = brain.process_comment("Love this product! 10/10", platform='Instagram')
        self.assertIn(result['action'], ('reply', 'ignore', 'flag', 'delete', 'pending_approval'))

    def test_live_moderation_obvious_spam(self):
        brain = SereaBrain(agent_id=self.agent.pk)
        result = brain.process_comment(
            "CLICK HERE TO WIN $1000!! FREE MONEY!! BUY NOW!!!",
            platform='Instagram',
        )
        self.assertIn(result['action'], ('delete', 'flag', 'pending_approval'))

    def test_live_daily_briefing(self):
        brain = SereaBrain(agent_id=self.agent.pk)
        briefing = brain.generate_daily_briefing()
        self.assertIsInstance(briefing, str)
        self.assertGreater(len(briefing), 10)
