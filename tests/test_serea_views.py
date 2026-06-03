import pytest
from django.urls import reverse
from serea.models import SereaAgent, ConversationMessage
from workspace_admin.models import HiredAIEmployee, AIEmployeeTier
from hub.models import BusinessInstance
from unittest.mock import patch, MagicMock, AsyncMock

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

@patch('serea.tasks.resume_after_approval.delay')
@patch('channels.layers.get_channel_layer')
def test_permission_respond_approve(mock_get_channel, mock_resume, agent_setup, client):
    user, agent = agent_setup
    
    mock_channel_layer = MagicMock()
    mock_channel_layer.group_send = AsyncMock()
    mock_get_channel.return_value = mock_channel_layer

    msg = ConversationMessage.objects.create(
        agent=agent, sender='serea', message_text="Pls approve",
        is_permission_request=True
    )
    
    client.force_login(user)
    response = client.post(
        reverse('serea:permission_respond', args=[msg.id]),
        {'decision': 'approve'},
        content_type='application/json',
    )

    assert response.status_code == 200
    msg.refresh_from_db()
    assert msg.permission_granted is True
    mock_resume.assert_called_with(msg.id)

    # Verify group_send broadcast for approval
    mock_channel_layer.group_send.assert_any_call(
        f'agent_{agent.id}',
        {
            'type': 'chat_message',
            'message': {
                'id': msg.id,
                'sender': msg.sender,
                'text': msg.message_text,
                'is_permission_request': True,
                'permission_granted': True,
                'created_at': msg.created_at.isoformat(),
            }
        }
    )

@patch('channels.layers.get_channel_layer')
def test_permission_respond_deny(mock_get_channel, client, agent_setup):
    user, agent = agent_setup
    client.force_login(user)
    
    mock_channel_layer = MagicMock()
    mock_channel_layer.group_send = AsyncMock()
    mock_get_channel.return_value = mock_channel_layer

    msg = ConversationMessage.objects.create(
        agent=agent, sender='serea', is_permission_request=True, message_text="Pls approve"
    )
    
    url = reverse('serea:permission_respond', kwargs={'msg_id': msg.id})
    response = client.post(url, {'decision': 'deny'}, content_type='application/json')
    
    assert response.status_code == 200
    assert response.json() == {'status': 'denied', 'message_id': msg.id}
    
    msg.refresh_from_db()
    assert msg.permission_granted is False
    
    # Verify denial message
    assert ConversationMessage.objects.filter(agent=agent, message_text__contains="skip this action").exists()

    # Verify group_send broadcast for denial
    mock_channel_layer.group_send.assert_any_call(
        f'agent_{agent.id}',
        {
            'type': 'chat_message',
            'message': {
                'id': msg.id,
                'sender': msg.sender,
                'text': msg.message_text,
                'is_permission_request': True,
                'permission_granted': False,
                'created_at': msg.created_at.isoformat(),
            }
        }
    )

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
    assert data['logs'][0]['action'] == 'deleted'
