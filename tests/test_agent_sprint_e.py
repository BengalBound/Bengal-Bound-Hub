import pytest
from django.urls import reverse
from unittest.mock import patch, MagicMock
from serea.models import SereaAgent, ConversationMessage
from workspace_admin.models import HiredAIEmployee, AIEmployeeTier
from hub.models import BusinessInstance
from agents.models import AgentCatalog, AgentInstance, AgentLog, AgentMemory
from tests.factories import UserFactory, BusinessInstanceFactory, BusinessEmployeeFactory, AgentCatalogFactory

pytestmark = pytest.mark.django_db

@pytest.fixture
def base_setup():
    user = UserFactory()
    biz = BusinessInstanceFactory(owner=user, slug='testbiz')
    employee = BusinessEmployeeFactory(business=biz, user=user, role='ceo')
    
    # Create tiers
    tier_intern = AIEmployeeTier.objects.create(name='intern', monthly_price_usd=0, token_limit=1000)
    tier_entry = AIEmployeeTier.objects.create(name='entry', monthly_price_usd=10, token_limit=5000)
    tier_mid = AIEmployeeTier.objects.create(name='mid', monthly_price_usd=25, token_limit=10000)
    
    # Create AgentCatalog item requiring entry tier
    catalog = AgentCatalogFactory(
        name='Aria', slug='aria', role='Customer Support',
        tier_required='entry', is_active=True
    )
    
    return {
        'user': user,
        'biz': biz,
        'employee': employee,
        'tier_intern': tier_intern,
        'tier_entry': tier_entry,
        'tier_mid': tier_mid,
        'catalog': catalog,
    }

def test_hire_ai_page_annotates_disabled_tiers(client, base_setup):
    user = base_setup['user']
    catalog = base_setup['catalog']
    
    client.force_login(user)
    url = reverse('console_admin:hire_ai') + f'?agent={catalog.slug}'
    response = client.get(url)
    
    assert response.status_code == 200
    tiers = response.context['tiers']
    
    # Tier 'intern' (rank 0) should be disabled because agent 'aria' requires 'entry' (rank 1)
    intern_tier = next(t for t in tiers if t.name == 'intern')
    assert intern_tier.is_disabled is True
    
    # Tier 'entry' (rank 1) should not be disabled
    entry_tier = next(t for t in tiers if t.name == 'entry')
    assert entry_tier.is_disabled is False

def test_hire_ai_flow_post_success(client, base_setup):
    user = base_setup['user']
    catalog = base_setup['catalog']
    tier_entry = base_setup['tier_entry']
    
    client.force_login(user)
    url = reverse('console_admin:hire_ai')
    
    response = client.post(url, {
        'tier_id': tier_entry.id,
        'duration_months': 1,
        'agent_slug': catalog.slug
    })
    
    # Successful hire redirects to the newly hired agent's workspace
    assert response.status_code == 302
    assert reverse('console_admin:agent_workspace', args=[catalog.slug]) in response.url
    
    # Verify HiredAIEmployee was created
    hired = HiredAIEmployee.objects.get(employer=user, agent_catalog=catalog)
    assert hired.ai_name == 'Aria'
    assert hired.tier == tier_entry
    
    # Signal should have provisioned SereaAgent
    agent = SereaAgent.objects.get(hired_employee=hired)
    assert agent.tenant == user
    assert agent.status == 'idle'
    
    # Signal should have provisioned AgentInstance
    instance = AgentInstance.objects.get(business=base_setup['biz'], catalog=catalog)
    assert instance.hired_employee == hired

@patch('serea.logic.SereaBrain.chat')
def test_agent_run_view_with_serea_agent(mock_chat, client, base_setup):
    user = base_setup['user']
    catalog = base_setup['catalog']
    tier_entry = base_setup['tier_entry']
    biz = base_setup['biz']
    
    mock_chat.return_value = "Hello! I am Aria."
    
    # Setup hired agent
    hired = HiredAIEmployee.objects.create(
        employer=user,
        tier=tier_entry,
        agent_catalog=catalog,
        ai_name='Aria'
    )
    # SereaAgent is auto-provisioned via signal, let's verify
    serea_agent = SereaAgent.objects.get(hired_employee=hired)
    
    # Let's ensure AgentInstance is also there
    instance = AgentInstance.objects.get(business=biz, catalog=catalog)
    
    client.force_login(user)
    url = f'/hub/{biz.slug}/agents/{catalog.slug}/api/run/'
    
    response = client.post(url, {'input': 'Who are you?'}, content_type='application/json')
    
    assert response.status_code == 200
    assert response.json()['result'] == "Hello! I am Aria."
    
    # Verify ConversationMessages are logged
    msgs = list(ConversationMessage.objects.filter(agent=serea_agent).order_by('created_at'))
    assert len(msgs) == 2
    assert msgs[0].sender == user.email
    assert msgs[0].message_text == 'Who are you?'
    assert msgs[1].sender == 'serea'
    assert msgs[1].message_text == 'Hello! I am Aria.'
    
    # Verify AgentLog is created
    log = AgentLog.objects.get(instance=instance)
    assert log.action == 'manual_run'
    assert log.outcome == 'success'
    assert log.detail == 'Hello! I am Aria.'

def test_agent_dashboard_view(client, base_setup):
    user = base_setup['user']
    catalog = base_setup['catalog']
    tier_entry = base_setup['tier_entry']
    biz = base_setup['biz']
    
    # Hire agent
    hired = HiredAIEmployee.objects.create(
        employer=user,
        tier=tier_entry,
        agent_catalog=catalog,
        ai_name='Aria'
    )
    instance = AgentInstance.objects.get(business=biz, catalog=catalog)
    
    # Add some log & memory data
    AgentLog.objects.create(instance=instance, action='manual_run', outcome='success', detail='Success run')
    AgentMemory.objects.create(instance=instance, subject='rules', memory_type='instruction', content='Always be polite')
    
    client.force_login(user)
    url = reverse('hub:agent_dashboard', kwargs={'slug': biz.slug, 'agent_slug': catalog.slug})
    response = client.get(url)
    
    assert response.status_code == 200
    assert catalog.name in response.content.decode()
    assert 'Success run' in response.content.decode()
    assert 'Always be polite' in response.content.decode()
