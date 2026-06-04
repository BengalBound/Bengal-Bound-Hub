import json
import pytest
from unittest.mock import patch
from hub.dashboard_configurator import DashboardConfigurator, DashboardAIModifier
from hub.models import BusinessInstance, DashboardConfig
from agents.models import AgentCatalog
from workspace_admin.models import HiredAIEmployee, AIEmployeeTier

pytestmark = pytest.mark.django_db

@pytest.fixture
def configurator_setup(user_factory):
    user = user_factory()
    biz = BusinessInstance.objects.create(owner=user, name="Config Biz", slug="config-biz")
    
    # Create required catalogs
    AgentCatalog.objects.create(slug="concierge", name="Concierge", is_active=True)
    AgentCatalog.objects.create(slug="serea-content", name="Serea Content", is_active=True)
    AgentCatalog.objects.create(slug="lead-hunter", name="Lead Hunter", is_active=True)
    AgentCatalog.objects.create(slug="custom-agent", name="Custom Agent", is_active=True)
    AgentCatalog.objects.create(slug="merch", name="Merch Agent", is_active=True)
    
    AIEmployeeTier.objects.create(name="intern", monthly_price_usd=0.00)
    AIEmployeeTier.objects.create(name="entry", monthly_price_usd=10.00)
    
    return user, biz

@patch('hub.dashboard_configurator.agent_chat')
def test_dashboard_configurator_default_flow(mock_chat, configurator_setup):
    user, biz = configurator_setup
    mock_chat.return_value = '{"widgets": [{"id": "modules_grid", "title": "Modules", "size": "large", "order": 1}], "layout": "standard_grid", "primary_color_suggestion": "#123456"}'
    
    configurator = DashboardConfigurator()
    answers = {
        'business_type': 'ecommerce',
        'main_challenge': 'getting_leads',
        'language': 'বাংলা',
        'payment_preference': 'bKash'
    }
    
    config = configurator.configure(biz, answers)
    
    # Check if currency is adapted
    assert config.currency == 'BDT'
    assert config.language == 'বাংলা'
    
    # Theme mapping for ecommerce should be applied
    assert config.dashboard_theme == 'ecommerce'
    assert config.primary_color == '#F97316'
    
    # Recommended agents logic check
    assert 'concierge' in config.recommended_agents
    
    # Verify starter agent activated
    assert HiredAIEmployee.objects.filter(employer=user, agent_catalog__slug=config.recommended_agents[0]).exists()

@patch('hub.dashboard_configurator.agent_chat')
def test_dashboard_configurator_fallback_layout(mock_chat, configurator_setup):
    user, biz = configurator_setup
    # Mock invalid JSON
    mock_chat.return_value = 'Invalid Response!'
    
    configurator = DashboardConfigurator()
    config = configurator.configure(biz, {'business_type': 'clinic'})
    
    assert config.layout['layout'] == 'standard_grid'
    assert len(config.layout['widgets']) == 3

@patch('hub.dashboard_configurator.agent_chat')
def test_dashboard_configurator_custom_agents(mock_chat, configurator_setup):
    user, biz = configurator_setup
    mock_chat.return_value = '{"layout": "standard"}'
    
    configurator = DashboardConfigurator()
    configurator.configure(
        biz, 
        {'business_type': 'other'}, 
        custom_agents=['custom-agent'], 
        agent_tiers={'custom-agent': 'entry'}
    )
    
    hired = HiredAIEmployee.objects.get(employer=user, agent_catalog__slug='custom-agent')
    assert hired.tier.name == 'entry'

@patch('hub.dashboard_configurator.agent_chat')
def test_dashboard_ai_modifier(mock_chat, configurator_setup):
    user, biz = configurator_setup
    DashboardConfig.objects.create(business=biz, layout={"layout": "old"}, dashboard_theme="default")
    
    mock_chat.return_value = '```json\n{"layout": {"layout": "new"}, "theme": "agency", "primary_color": "#000000", "message": "Updated!"}\n```'
    
    modifier = DashboardAIModifier()
    result = modifier.modify(biz, "Make my theme agency and layout new")
    
    assert result['success'] is True
    assert result['message'] == "Updated!"
    
    config = DashboardConfig.objects.get(business=biz)
    assert config.layout == {"layout": "new"}
    assert config.dashboard_theme == "agency"
    assert config.primary_color == "#000000"

def test_dashboard_ai_modifier_no_config(configurator_setup):
    user, biz = configurator_setup
    modifier = DashboardAIModifier()
    result = modifier.modify(biz, "Change theme")
    assert result['success'] is False
    assert "not found" in result['message']
