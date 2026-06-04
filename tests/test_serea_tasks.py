import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from serea.tasks import (
    monitor_social_task, execute_content_task, daily_briefing_task,
    generate_daily_report_task, resume_after_approval, process_chat_message_task,
    dispatch_monitor_to_all_agents, dispatch_content_to_all_agents,
    dispatch_briefing_to_all_agents, dispatch_reports_to_all_agents,
    _fetch_comments_from_platforms, _execute_moderation_action,
    _publish_content_item
)
from serea.models import SereaAgent, ContentQueue, DailyReport, ConversationMessage, SereaTask, ModerationLog, SocialMediaAccount

pytestmark = pytest.mark.django_db

@patch('serea.tasks._fetch_comments_from_platforms')
@patch('serea.logic.SereaBrain.process_comment')
@patch('serea.tasks._execute_moderation_action')
def test_monitor_social_task(mock_exec, mock_process, mock_fetch, agent_setup):
    user, agent = agent_setup
    
    # Empty
    mock_fetch.return_value = []
    monitor_social_task.apply(args=[agent.id])
    
    # 1 comment
    mock_fetch.return_value = [{'text': 'Hello', 'platform': 'Facebook', 'account_pk': 1, 'api_platform': 'facebook', 'comment_id': 'c1', 'post_id': 'p1'}]
    mock_process.return_value = {'action': 'reply', 'response_text': 'Hi'}
    monitor_social_task.apply(args=[agent.id])
    
    assert ModerationLog.objects.filter(agent=agent, action_taken='reply').exists()
    mock_exec.assert_called_once()
    
    # Test token limit exceeded
    from serea.logic import TokenLimitExceeded
    mock_process.side_effect = TokenLimitExceeded("Too many tokens")
    monitor_social_task.apply(args=[agent.id])
    assert ConversationMessage.objects.filter(agent=agent, message_text="Too many tokens").exists()

@patch('serea.tasks.get_adapter')
def test_fetch_comments_from_platforms(mock_get_adapter, agent_setup):
    user, agent = agent_setup
    account = SocialMediaAccount.objects.create(agent=agent, platform='facebook', is_active=True, status='connected')
    mock_adapter = MagicMock()
    mock_adapter.fetch_recent_comments.return_value = [{'text': 'T1', 'id': 'C1', 'post_id': 'P1'}]
    mock_get_adapter.return_value = mock_adapter
    
    res = _fetch_comments_from_platforms(agent, ['facebook'])
    assert len(res) == 1
    assert res[0]['text'] == 'T1'

@patch('serea.tasks.get_adapter')
def test_execute_moderation_action(mock_get_adapter, agent_setup):
    user, agent = agent_setup
    account = SocialMediaAccount.objects.create(agent=agent, platform='facebook', is_active=True, status='connected')
    mock_adapter = MagicMock()
    mock_get_adapter.return_value = mock_adapter
    
    _execute_moderation_action(agent, {'api_platform': 'facebook', 'comment_id': 'C1', 'account_pk': account.pk}, {'action': 'delete'})
    mock_adapter.delete_comment.assert_called_with('C1')
    
    _execute_moderation_action(agent, {'api_platform': 'facebook', 'comment_id': 'C1', 'account_pk': account.pk}, {'action': 'reply', 'response_text': 'Hi'})
    mock_adapter.reply_to_comment.assert_called_with('C1', 'Hi')

@patch('serea.tasks._publish_content_item')
def test_execute_content_task(mock_publish, agent_setup):
    user, agent = agent_setup
    ContentQueue.objects.create(agent=agent, title="T1", platform="Facebook", status="pending", post_date=timezone.now())
    
    mock_publish.return_value = "post123"
    execute_content_task.apply(args=[agent.id])
    
    assert ContentQueue.objects.filter(agent=agent, status='posted').exists()
    
    # Test failure
    ContentQueue.objects.create(agent=agent, title="T2", platform="Facebook", status="pending", post_date=timezone.now())
    mock_publish.side_effect = Exception("Failed")
    with patch('serea.tasks.execute_content_task.retry') as mock_retry:
        execute_content_task.apply(args=[agent.id])
        mock_retry.assert_called()

@patch('serea.tasks.get_adapter')
def test_publish_content_item(mock_get_adapter, agent_setup):
    user, agent = agent_setup
    SocialMediaAccount.objects.create(agent=agent, platform='facebook', is_active=True, status='connected')
    item = ContentQueue.objects.create(agent=agent, title="T1", platform="Facebook", caption="Cap", status="pending", post_date=timezone.now())
    
    mock_adapter = MagicMock()
    mock_adapter.post.return_value = MagicMock(success=True, platform_post_id="post1")
    mock_get_adapter.return_value = mock_adapter
    
    mock_brain = MagicMock()
    res = _publish_content_item(item, mock_brain)
    assert res == "post1"

@patch('serea.logic.SereaBrain.generate_daily_briefing')
def test_daily_briefing_task(mock_gen, agent_setup):
    user, agent = agent_setup
    mock_gen.return_value = "Morning!"
    daily_briefing_task.apply(args=[agent.id])
    
    assert ConversationMessage.objects.filter(agent=agent, message_text="Morning!").exists()

@patch('serea.logic.SereaBrain._run')
def test_generate_daily_report_task(mock_run, agent_setup):
    user, agent = agent_setup
    
    SereaTask.objects.create(agent=agent, title="T1", status="done")
    ContentQueue.objects.create(agent=agent, title="C1", status="posted", post_date=timezone.now())
    ModerationLog.objects.create(agent=agent, platform="Facebook", comment_text="Test", action_taken="reply")
    
    mock_run.return_value = ("Summary text", None)
    generate_daily_report_task.apply(args=[agent.id])
    
    report = DailyReport.objects.filter(agent=agent).first()
    assert report is not None
    assert report.items.count() > 0

@patch('serea.logic.SereaBrain._run')
def test_resume_after_approval(mock_run, agent_setup):
    user, agent = agent_setup
    msg = ConversationMessage.objects.create(agent=agent, is_permission_request=True, permission_granted=True, pending_action_context={'raw_context': 'Do it'})
    
    mock_run.return_value = ("Action completed", None)
    resume_after_approval.apply(args=[msg.id])
    
    assert ConversationMessage.objects.filter(message_text__contains="Action completed").exists()

@patch('serea.logic.SereaBrain.chat')
def test_process_chat_message_task(mock_chat, agent_setup):
    user, agent = agent_setup
    mock_chat.return_value = "Reply msg"
    process_chat_message_task.apply(args=[agent.id, "Hi Serea", user.email])
    
    assert ConversationMessage.objects.filter(message_text="Reply msg").exists()

@patch('serea.tasks.monitor_social_task.delay')
@patch('serea.tasks.execute_content_task.delay')
@patch('serea.tasks.daily_briefing_task.delay')
@patch('serea.tasks.generate_daily_report_task.delay')
def test_dispatch_tasks(m4, m3, m2, m1, agent_setup):
    dispatch_monitor_to_all_agents.apply()
    dispatch_content_to_all_agents.apply()
    dispatch_briefing_to_all_agents.apply()
    dispatch_reports_to_all_agents.apply()
    m1.assert_called()
    m2.assert_called()
    m3.assert_called()
    m4.assert_called()
