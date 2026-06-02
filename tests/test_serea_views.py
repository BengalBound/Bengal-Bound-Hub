import pytest
from django.urls import reverse
from serea.models import SereaAgent, ConversationMessage
from workspace_admin.models import HiredAIEmployee, AIEmployeeTier
from hub.models import BusinessInstance
from unittest.mock import patch

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

@patch('serea.views.resume_after_approval.delay')
def test_permission_respond_approve(mock_resume, agent_setup, client):
    user, agent = agent_setup
    
    msg = ConversationMessage.objects.create(
        agent=agent, sender='serea', message_text="Pls approve",
        is_permission_request=True
    )
    
    client.force_login(user)
    response = client.post(reverse('serea:permission_respond', args=[msg.id]), {
        'action': 'approve'
    })
    
    assert response.status_code == 200
    msg.refresh_from_db()
    assert msg.permission_granted is True
    mock_resume.assert_called_with(msg.id)

def test_permission_respond_deny(client, agent_setup):
    user, agent = agent_setup
    client.force_login(user)
    
    msg = ConversationMessage.objects.create(
        agent=agent, sender='serea', is_permission_request=True
    )
    
    url = reverse('serea:permission_respond', kwargs={'msg_id': msg.id})
    response = client.post(url, {'decision': 'deny'}, content_type='application/json')
    
    assert response.status_code == 200
    assert response.json() == {'status': 'denied', 'message_id': msg.id}
    
    msg.refresh_from_db()
    assert msg.permission_granted is False
    
    # Verify denial message
    assert ConversationMessage.objects.filter(agent=agent, message_text__contains="skip this action").exists()

def test_permission_respond_invalid(client, agent_setup):
    user, agent = agent_setup
    client.force_login(user)
    
    msg = ConversationMessage.objects.create(
        agent=agent, sender='serea', is_permission_request=True
    )
    
    url = reverse('serea:permission_respond', kwargs={'msg_id': msg.id})
    response = client.post(url, {'decision': 'invalid'}, content_type='application/json')
    
    assert response.status_code == 400
    assert 'decision must be' in response.json()['error']

def test_agent_chat_poll(client, agent_setup):
    user, agent = agent_setup
    client.force_login(user)
    
    ConversationMessage.objects.create(agent=agent, sender='user', message_text='Hello')
    
    url = reverse('serea:agent_chat', kwargs={'agent_id': agent.id})
    response = client.get(url)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data['messages']) == 1
    assert data['messages'][0]['text'] == 'Hello'

def test_agent_logs(client, agent_setup):
    user, agent = agent_setup
    client.force_login(user)
    
    from serea.models import ModerationLog
    ModerationLog.objects.create(agent=agent, platform='Facebook', action_taken='deleted')
    
    url = reverse('serea:agent_logs', kwargs={'agent_id': agent.id})
    response = client.get(url)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data['logs']) == 1
    assert data['logs'][0]['action_taken'] == 'deleted'
