import pytest
from unittest.mock import patch, MagicMock
from serea.tasks import (
    monitor_social_task, execute_content_task, daily_briefing_task,
    generate_daily_report_task, resume_after_approval, dispatch_monitor_to_all_agents
)
from serea.models import SereaAgent, ContentQueue, ModerationLog, ConversationMessage, SereaTask
from workspace_admin.models import HiredAIEmployee, AIEmployeeTier
from hub.models import BusinessInstance
from django.utils import timezone

pytestmark = pytest.mark.django_db

@pytest.fixture
def agent_setup(user_factory):
    user = user_factory()
    biz = BusinessInstance.objects.create(owner=user, name='Biz', slug='biz')
    tier = AIEmployeeTier.objects.create(name='entry', monthly_price_usd=0)
    hired = HiredAIEmployee.objects.create(employer=user, ai_name='Serea', tier=tier)
    agent = SereaAgent.objects.get(hired_employee=hired)
    agent.status = 'idle'
    agent.save()
    return user, agent

@patch('serea.tasks.SereaBrain')
@patch('serea.tasks._fetch_comments_from_platforms')
def test_monitor_social_task(mock_fetch, mock_brain_cls, agent_setup):
    user, agent = agent_setup
    
    mock_fetch.return_value = [{'text': 'Bad comment!', 'platform': 'Facebook', 'comment_id': '1'}]
    
    mock_brain = MagicMock()
    mock_brain.process_comment.return_value = {'action': 'deleted', 'sentiment': -0.9, 'confidence': 0.9}
    mock_brain_cls.return_value = mock_brain
    
    with patch('serea.tasks._execute_moderation_action') as mock_exec, \
         patch('serea.tasks.monitor_social_task.retry') as mock_retry:
        monitor_social_task.apply(args=[agent.id])
        
        # Check if retry was called (meaning an exception occurred)
        if mock_retry.called:
            print("Retry called with:", mock_retry.call_args)
            assert False, "Exception occurred inside task, triggering retry"
            
        # Verify brain was called
        mock_brain.process_comment.assert_called_with('Bad comment!', platform='Facebook')
        
        # Verify moderation log created
        assert ModerationLog.objects.filter(agent=agent, action_taken='deleted').exists()
        
        # Verify execution
        mock_exec.assert_called_once()

@patch('serea.tasks.SereaBrain')
@patch('serea.tasks._publish_content_item')
def test_execute_content_task(mock_publish, mock_brain_cls, agent_setup):
    user, agent = agent_setup
    
    # Create pending content
    item = ContentQueue.objects.create(
        agent=agent, title='Promo', platform='Facebook', status='pending',
        post_date=timezone.now() - timezone.timedelta(minutes=5)
    )
    
    mock_publish.return_value = 'post_123'
    
    with patch('serea.tasks.execute_content_task.retry') as mock_retry:
        execute_content_task.apply(args=[agent.id])
        if mock_retry.called:
            print("Retry called with:", mock_retry.call_args)
            assert False, "Exception occurred inside execute_content_task"
    
    item.refresh_from_db()
    assert item.status == 'posted'
    assert item.platform_post_id == 'post_123'

@patch('serea.tasks.SereaBrain')
def test_daily_briefing_task(mock_brain_cls, agent_setup):
    user, agent = agent_setup
    
    mock_brain = MagicMock()
    mock_brain.generate_daily_briefing.return_value = "Good morning! All is well."
    mock_brain_cls.return_value = mock_brain
    
    daily_briefing_task.apply(args=[agent.id])
    
    assert ConversationMessage.objects.filter(agent=agent, sender='serea', message_text__contains="Good morning").exists()

@patch('serea.tasks.SereaBrain')
def test_generate_daily_report_task(mock_brain_cls, agent_setup):
    user, agent = agent_setup
    
    SereaTask.objects.create(agent=agent, title='Fix stuff', status='done')
    
    mock_brain = MagicMock()
    mock_brain._run.return_value = ("Here is your wrap up.", None)
    mock_brain_cls.return_value = mock_brain
    
    generate_daily_report_task.apply(args=[agent.id])
    
    from serea.models import DailyReport, DailyReportItem
    report = DailyReport.objects.filter(agent=agent).first()
    assert report is not None
    assert report.items.count() > 0

@patch('serea.tasks.SereaBrain')
def test_resume_after_approval(mock_brain_cls, agent_setup):
    user, agent = agent_setup
    
    msg = ConversationMessage.objects.create(
        agent=agent, sender='serea', message_text="Please approve.",
        is_permission_request=True, permission_granted=True,
        pending_action_context={"raw_context": "do it"}
    )
    
    mock_brain = MagicMock()
    mock_brain._run.return_value = ("Done!", None)
    mock_brain_cls.return_value = mock_brain
    
    resume_after_approval.apply(args=[msg.id])
    
    assert ConversationMessage.objects.filter(agent=agent, sender='serea', message_text__contains="Done!").exists()
        
@patch('serea.tasks.monitor_social_task.delay')
def test_dispatch_monitor_to_all_agents(mock_delay, agent_setup):
    user, agent = agent_setup
    
    dispatch_monitor_to_all_agents.apply()
    mock_delay.assert_called_with(agent.id)
