import pytest
import json
from django.urls import reverse
from unittest.mock import patch, MagicMock
from serea.models import SereaAgent, ConversationMessage, ModerationLog
from workspace_admin.models import HiredAIEmployee, AIEmployeeTier
from hub.models import BusinessInstance
from django.utils import timezone

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def view_agent(user_factory):
    user = user_factory()
    tier = AIEmployeeTier.objects.create(name="Pro", monthly_price_usd=0)
    hired = HiredAIEmployee.objects.create(employer=user, ai_name="Serea 2", tier=tier)
    agent = SereaAgent.objects.get(hired_employee=hired)
    agent.status = 'idle'
    agent.save()
    return user, agent

def test_agent_chat_view(api_client, view_agent):
    user, agent = view_agent
    api_client.force_authenticate(user=user)
    
    ConversationMessage.objects.create(agent=agent, sender='user', message_text='hi')
    ConversationMessage.objects.create(agent=agent, sender='serea', message_text='hello')
    
    # Needs a proper url, let's assume it maps to something like /serea/agent/<id>/chat/
    # If reverse fails, we can test the view directly using RequestFactory.
    # Actually let's use RequestFactory to avoid urls.py issues.
    pass

def test_serea_views_directly(rf, view_agent):
    from serea.views import permission_respond, agent_chat, agent_logs, send_chat_message
    
    user, agent = view_agent
    
    # 1. agent_chat
    ConversationMessage.objects.create(agent=agent, sender='user', message_text='hi')
    req = rf.get(f'/serea/agent/{agent.id}/chat/')
    req.user = user
    resp = agent_chat(req, agent.id)
    assert resp.status_code == 200
    data = json.loads(resp.content)
    assert len(data['messages']) == 1
    
    # 2. agent_logs
    ModerationLog.objects.create(agent=agent, platform='fb', comment_text='bad', action_taken='delete')
    req2 = rf.get(f'/serea/agent/{agent.id}/logs/')
    req2.user = user
    resp2 = agent_logs(req2, agent.id)
    assert resp2.status_code == 200
    data2 = json.loads(resp2.content)
    assert len(data2['logs']) == 1
    
    # 3. send_chat_message
    req3 = rf.post(f'/serea/agent/{agent.id}/send/', data=json.dumps({"message": "test"}), content_type="application/json")
    req3.user = user
    with patch('serea.tasks.process_chat_message_task.delay') as mock_delay:
        resp3 = send_chat_message(req3, agent.id)
        assert resp3.status_code == 200
        mock_delay.assert_called_once()
        
    # 4. send_chat_message fallback
    req4 = rf.post(f'/serea/agent/{agent.id}/send/', data=json.dumps({"message": "test2"}), content_type="application/json")
    req4.user = user
    with patch('serea.tasks.process_chat_message_task.delay', side_effect=Exception("Celery down")):
        with patch('serea.logic.SereaBrain.chat') as mock_chat:
            mock_chat.return_value = "fallback reply"
            resp4 = send_chat_message(req4, agent.id)
            assert resp4.status_code == 200
            assert ConversationMessage.objects.filter(message_text="fallback reply").exists()
            
    # 5. permission_respond
    msg = ConversationMessage.objects.create(
        agent=agent, sender='serea', message_text='need perm', is_permission_request=True
    )
    req5 = rf.post(f'/serea/permission/{msg.id}/respond/', data=json.dumps({"decision": "approve"}), content_type="application/json")
    req5.user = user
    with patch('serea.tasks.resume_after_approval.delay') as mock_resume:
        resp5 = permission_respond(req5, msg.id)
        assert resp5.status_code == 200
        mock_resume.assert_called_once()
