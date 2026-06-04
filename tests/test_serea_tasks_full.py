import pytest
from unittest.mock import patch, MagicMock
from serea.tasks import monitor_social_task, execute_content_task, daily_briefing_task, resume_after_approval, process_chat_message_task
from serea.models import SereaAgent, SocialMediaAccount, ModerationLog, ConversationMessage

pytestmark = pytest.mark.django_db

def test_monitor_social_task(agent_setup):
    user, agent = agent_setup
    
    # Offline agent
    agent.status = 'offline'
    agent.save()
    monitor_social_task(agent.id)
    
    agent.status = 'idle'
    agent.save()
    
    with patch('serea.tasks._fetch_comments_from_platforms') as mock_fetch:
        mock_fetch.return_value = [{'text': 'test', 'platform': 'facebook', 'comment_id': '1', 'post_id': '2', 'account_pk': 1, 'api_platform': 'facebook'}]
        with patch('serea.tasks.SereaBrain.process_comment') as mock_process:
            mock_process.return_value = {'action': 'ignore', 'confidence': 0.99, 'sentiment': 0.8, 'requires_human': False}
            with patch('serea.tasks._execute_moderation_action') as mock_exec:
                monitor_social_task(agent.id)
                assert ModerationLog.objects.filter(agent=agent, comment_text='test').exists()
                assert mock_exec.called

def test_resume_after_approval(agent_setup):
    user, agent = agent_setup
    msg = ConversationMessage.objects.create(agent=agent, sender='serea', message_text='perm', is_permission_request=True, permission_granted=True, pending_action_context={'action': 'delete', 'platform': 'facebook', 'comment_id': '123'})
    SocialMediaAccount.objects.create(agent=agent, platform='facebook', account_id='p1', status='connected')
    with patch('serea.logic.SereaBrain._run', return_value=("deleted", None)):
        resume_after_approval(msg.id)
        assert ConversationMessage.objects.filter(message_text__contains='deleted').exists()

def test_process_chat_message_task(agent_setup):
    user, agent = agent_setup
    with patch('serea.logic.SereaBrain.chat') as mock_chat:
        mock_chat.return_value = "hello task"
        process_chat_message_task(agent.id, "ping", "test@test.com")
        assert ConversationMessage.objects.filter(message_text="hello task").exists()

def test_daily_briefing_task(agent_setup):
    user, agent = agent_setup
    with patch('serea.logic.SereaBrain.generate_daily_briefing') as mock_brief:
        mock_brief.return_value = "Morning briefing"
        daily_briefing_task(agent.id)
        assert ConversationMessage.objects.filter(message_text="Morning briefing").exists()

def test_execute_content_task(agent_setup):
    user, agent = agent_setup
    from serea.models import ContentQueue
    from django.utils import timezone
    q = ContentQueue.objects.create(agent=agent, platform='Facebook', status='pending', post_date=timezone.now(), caption='hi')
    with patch('serea.tasks.get_adapter') as mock_adapter:
        mock_ad = MagicMock()
        mock_ad.post.return_value = MagicMock(success=True, platform_post_id='123', url='http://fb')
        mock_adapter.return_value = mock_ad
        SocialMediaAccount.objects.create(agent=agent, platform='facebook', account_id='p1', status='connected')
        with patch('serea.logic.SereaBrain._run', return_value=("caption", None)):
            execute_content_task(agent.id)
            q.refresh_from_db()
            assert q.status == 'posted'
