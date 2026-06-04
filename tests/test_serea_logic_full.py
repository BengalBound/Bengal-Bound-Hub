import pytest
from unittest.mock import patch, MagicMock
from serea.logic import SereaBrain, TokenLimitExceeded
from serea.models import SereaAgent
from hub.models import BusinessInstance
from workspace_admin.models import HiredAIEmployee, AIEmployeeTier

pytestmark = pytest.mark.django_db

@pytest.fixture
def logic_agent(user_factory):
    user = user_factory()
    biz = BusinessInstance.objects.create(owner=user, name="L Biz", slug="l-biz")
    tier = AIEmployeeTier.objects.create(name="entry", monthly_price_usd=0)
    hired = HiredAIEmployee.objects.create(employer=user, ai_name="L Serea", tier=tier)
    agent = SereaAgent.objects.get(hired_employee=hired)
    agent.status = 'idle'
    agent.save()
    return agent

@patch('serea.logic.ChatOpenAI')
@patch('serea.logic.create_react_agent')
def test_serea_brain_init_and_run(mock_create_react, mock_chat, logic_agent):
    mock_llm = MagicMock()
    mock_chat.return_value = mock_llm
    
    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {"messages": [MagicMock(content="Hello LLM")]}
    mock_create_react.return_value = mock_agent
    
    brain = SereaBrain(agent_id=logic_agent.id)
    
    # Test chat
    reply = brain.chat("Hi")
    assert reply == "Hello LLM"
    
    # Test process_comment
    mock_agent.invoke.return_value = {"messages": [MagicMock(content="""```json\n{"action": "reply", "sentiment": 0.5, "confidence": 0.9, "response_text": "hi"}```""")]}
    res = brain.process_comment("test comment", "facebook")
    assert res['action'] == 'reply'
    
    # Test daily briefing
    mock_agent.invoke.return_value = {"messages": [MagicMock(content="Good morning")]}
    briefing = brain.generate_daily_briefing()
    assert briefing == "Good morning"
