import pytest
import json
from django.urls import reverse
from unittest.mock import patch
from serea.models import SocialMediaAccount, ConversationMessage
from django.test import override_settings

pytestmark = pytest.mark.django_db(transaction=True)

@pytest.fixture
def facebook_account(agent_setup):
    user, agent = agent_setup
    return SocialMediaAccount.objects.create(
        agent=agent,
        platform='facebook',
        account_id='page_123',
        access_token='token123',
        status='connected'
    )

@pytest.fixture
def instagram_account(agent_setup):
    user, agent = agent_setup
    return SocialMediaAccount.objects.create(
        agent=agent,
        platform='instagram',
        account_id='ig_123',
        access_token='token123',
        status='connected'
    )

@override_settings(FACEBOOK_WEBHOOK_VERIFY_TOKEN='serea_webhook_verify')
def test_facebook_webhook_get(client):
    response = client.get('/serea/webhook/facebook/?hub.mode=subscribe&hub.verify_token=serea_webhook_verify&hub.challenge=1234')
    assert response.status_code == 200
    assert response.content == b'1234'

    response_fail = client.get('/serea/webhook/facebook/?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=1234')
    assert response_fail.status_code == 403

def test_facebook_webhook_post(client, facebook_account):
    payload = {
        "object": "page",
        "entry": [{
            "id": "page_123",
            "messaging": [{
                "sender": {"id": "user_456"},
                "message": {"text": "hello fb"}
            }]
        }]
    }
    with patch('serea.views._send_facebook_reply', return_value=True) as mock_send:
        with patch('serea.logic.SereaBrain.reply_to_customer_dm', return_value="hello back") as mock_reply:
            response = client.post('/serea/webhook/facebook/', data=json.dumps(payload), content_type='application/json')
            assert response.status_code == 200
            
            import time
            time.sleep(1.0) # Wait for thread
            
            assert mock_reply.called
            assert mock_send.called
            
            msgs = ConversationMessage.objects.filter(sender='facebook_user:user_456')
            assert msgs.exists()

@override_settings(INSTAGRAM_WEBHOOK_VERIFY_TOKEN='serea_webhook_verify')
def test_instagram_webhook_get(client):
    response = client.get('/serea/webhook/instagram/?hub.mode=subscribe&hub.verify_token=serea_webhook_verify&hub.challenge=5678')
    assert response.status_code == 200
    assert response.content == b'5678'

    response_fail = client.get('/serea/webhook/instagram/?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=5678')
    assert response_fail.status_code == 403

def test_instagram_webhook_post_dm(client, instagram_account):
    payload = {
        "object": "instagram",
        "entry": [{
            "id": "ig_123",
            "messaging": [{
                "sender": {"id": "ig_user_456"},
                "message": {"text": "hello ig"}
            }]
        }]
    }
    with patch('serea.views._send_instagram_reply', return_value=True) as mock_send:
        with patch('serea.logic.SereaBrain.reply_to_customer_dm', return_value="hello back ig") as mock_reply:
            response = client.post('/serea/webhook/instagram/', data=json.dumps(payload), content_type='application/json')
            assert response.status_code == 200
            
            import time
            time.sleep(1.0) # Wait for thread
            
            assert mock_reply.called
            assert mock_send.called
            
            msgs = ConversationMessage.objects.filter(sender='instagram_user:ig_user_456')
            assert msgs.exists()
