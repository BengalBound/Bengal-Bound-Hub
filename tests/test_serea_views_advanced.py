import json
import pytest
from unittest.mock import patch
from django.urls import reverse
from serea.models import SereaAgent, ConversationMessage, SocialMediaAccount
from workspace_admin.models import HiredAIEmployee, AIEmployeeTier
from hub.models import BusinessInstance

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

@patch('serea.tasks.process_chat_message_task.delay')
def test_send_chat_message_async(mock_delay, client, agent_setup):
    user, agent = agent_setup
    client.force_login(user)

    url = reverse('serea:send_chat_message', kwargs={'agent_id': agent.id})
    response = client.post(url, json.dumps({'message': 'Hello Serea'}), content_type='application/json')
    
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert data['async'] is True
    mock_delay.assert_called_once()
    
    assert ConversationMessage.objects.filter(agent=agent, message_text='Hello Serea').exists()

from django.test import override_settings

@patch('serea.tasks.process_chat_message_task.delay')
@patch('serea.logic.SereaBrain.chat')
def test_send_chat_message_sync_fallback(mock_chat, mock_delay, client, agent_setup):
    user, agent = agent_setup
    client.force_login(user)
    
    # Force Celery delay to raise Exception so fallback triggers
    mock_delay.side_effect = Exception("Celery unavailable")
    mock_chat.return_value = "Fallback reply!"

    url = reverse('serea:send_chat_message', kwargs={'agent_id': agent.id})
    response = client.post(url, json.dumps({'message': 'Hello Sync'}), content_type='application/json')
    
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert data['async'] is False
    
    assert ConversationMessage.objects.filter(agent=agent, message_text='Fallback reply!').exists()

def test_send_chat_message_offline(client, agent_setup):
    user, agent = agent_setup
    client.force_login(user)
    agent.status = 'offline'
    agent.save()

    url = reverse('serea:send_chat_message', kwargs={'agent_id': agent.id})
    response = client.post(url, json.dumps({'message': 'Hey'}), content_type='application/json')
    assert response.status_code == 403

@override_settings(FACEBOOK_WEBHOOK_VERIFY_TOKEN='test_token')
def test_facebook_webhook_verification(client):
    url = reverse('serea:facebook_webhook')
    response = client.get(url, {'hub.mode': 'subscribe', 'hub.verify_token': 'test_token', 'hub.challenge': '123'})
    assert response.status_code == 200
    assert response.content == b'123'

@patch('serea.views._handle_facebook_dm')
def test_facebook_webhook_event(mock_handle, client):
    url = reverse('serea:facebook_webhook')
    payload = {
        'object': 'page',
        'entry': [{
            'id': 'page123',
            'messaging': [{
                'sender': {'id': 'user456'},
                'message': {'text': 'Hello fb'}
            }]
        }]
    }
    response = client.post(url, json.dumps(payload), content_type='application/json')
    assert response.status_code == 200

@override_settings(INSTAGRAM_WEBHOOK_VERIFY_TOKEN='test_token', FACEBOOK_WEBHOOK_VERIFY_TOKEN='test_token')
def test_instagram_webhook_verification(client):
    url = reverse('serea:instagram_webhook')
    response = client.get(url, {'hub.mode': 'subscribe', 'hub.verify_token': 'test_token', 'hub.challenge': '456'})
    assert response.status_code == 200
    assert response.content == b'456'

@patch('serea.logic.SereaBrain.process_comment')
def test_trigger_linkedin_moderation(mock_process, client, agent_setup):
    user, agent = agent_setup
    client.force_login(user)
    
    mock_process.return_value = {'action': 'deleted', 'confidence': 0.99}

    url = reverse('serea:linkedin_moderate', kwargs={'agent_id': agent.id})
    payload = {'comment_text': 'Bad comment', 'comment_url': 'http://linkedin.com'}
    response = client.post(url, json.dumps(payload), content_type='application/json')
    
    assert response.status_code == 200
    assert response.json()['action'] == 'deleted'

@patch('serea.views._send_facebook_reply')
@patch('serea.logic.SereaBrain.reply_to_customer_dm')
def test_handle_facebook_dm(mock_reply_dm, mock_send_fb, agent_setup):
    from serea.views import _handle_facebook_dm
    user, agent = agent_setup
    SocialMediaAccount.objects.create(agent=agent, platform='facebook', account_id='page123', status='connected')
    
    mock_reply_dm.return_value = "Hello back!"
    mock_send_fb.return_value = True
    
    _handle_facebook_dm('page123', 'sender456', 'Hello')
    
    assert ConversationMessage.objects.filter(message_text="Hello back!").exists()

@patch('serea.views._send_instagram_reply')
@patch('serea.logic.SereaBrain.reply_to_customer_dm')
def test_handle_instagram_dm(mock_reply_dm, mock_send_ig, agent_setup):
    from serea.views import _handle_instagram_dm
    user, agent = agent_setup
    SocialMediaAccount.objects.create(agent=agent, platform='instagram', account_id='ig123', status='connected')
    
    mock_reply_dm.return_value = "IG Reply!"
    mock_send_ig.return_value = True
    
    _handle_instagram_dm('ig123', 'sender456', 'Hello IG')
    
    assert ConversationMessage.objects.filter(message_text="IG Reply!").exists()

@patch('serea.logic.SereaBrain.process_comment')
def test_handle_instagram_comment(mock_process, agent_setup):
    from serea.views import _handle_instagram_comment
    user, agent = agent_setup
    SocialMediaAccount.objects.create(agent=agent, platform='instagram', account_id='ig123', status='connected')
    
    mock_process.return_value = {'action': 'kept', 'confidence': 0.8}
    
    _handle_instagram_comment('ig123', {'text': 'Nice pic'})
    
    from serea.models import ModerationLog
    assert ModerationLog.objects.filter(platform='Instagram', action_taken='kept').exists()
