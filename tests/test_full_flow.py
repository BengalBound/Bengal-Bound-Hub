import pytest
from django.urls import reverse
from hub.models import BusinessInstance, BusinessEmployee, ModuleCatalog, TenantModule
from workspace_admin.models import HiredAIEmployee, AIEmployeeTier
from agents.models import AgentCatalog, AgentInstance

pytestmark = pytest.mark.django_db

def test_full_business_and_agent_flow(client, user_factory, mocker):
    """
    Test the complete user journey:
    1. Sign up/Login
    2. Create a Business (Tenant)
    3. Verify Employee access
    4. Activate a module
    5. Hire an AI agent
    6. Simulate interacting with the agent (using pytest-mock)
    """
    # 1. User signs up & logs in
    user = user_factory(email="founder@acme.com")
    client.force_login(user)

    # 2. User creates a Business
    # We'll use the hub creation endpoint if one exists, or simulate creating it directly
    # For now, we simulate the backend creation
    business = BusinessInstance.objects.create(
        owner=user,
        name='Acme Corp',
        slug='acme-corp',
        business_type='business'
    )
    
    assert BusinessInstance.objects.filter(slug='acme-corp').exists()
    assert business.owner == user

    # 3. Verify BusinessEmployee assignment with owner access
    employee = BusinessEmployee.objects.create(
        business=business,
        user=user,
        name='Founder',
        role='ceo'
    )
    assert employee.role == 'ceo'
    assert employee.access_level == 9  # CEO level

    # 4. Activate a module
    catalog_module = ModuleCatalog.objects.create(
        module_id='crm', name='CRM', category='sales', is_available=True, is_free=True
    )
    TenantModule.objects.create(
        business=business,
        module=catalog_module,
        tier='free'
    )
    assert TenantModule.objects.filter(business=business, module__module_id='crm').exists()

    # 5. Hire an AI agent
    tier = AIEmployeeTier.objects.create(name='entry', description='Entry Level', monthly_price_usd=0)
    agent_catalog = AgentCatalog.objects.create(
        name='Crux', slug='crux', role='CRM Manager', tier_required='entry'
    )
    
    hired_agent = HiredAIEmployee.objects.create(
        employer=user,
        ai_name='Crux',
        tier=tier
    )
    assert HiredAIEmployee.objects.filter(employer=user, ai_name='Crux').exists()

    # Also create an AgentInstance linking the business and catalog
    agent_instance = AgentInstance.objects.create(
        business=business,
        hired_employee=hired_agent,
        catalog=agent_catalog,
        status='idle'
    )
    assert AgentInstance.objects.filter(business=business, catalog__slug='crux').exists()

    # 6. Simulate an AI interaction using pytest-mock
    # We mock out create_agent from langchain so it doesn't make a real network request
    mock_create_agent = mocker.patch('langchain.agents.create_agent')
    mock_agent = mocker.Mock()
    # The agent returns a dictionary with messages
    mock_agent.invoke.return_value = {
        "messages": [mocker.Mock(content="Hello! I am Crux.")]
    }
    mock_create_agent.return_value = mock_agent

    from agents.utils import agent_chat
    response = agent_chat(messages=[{"role": "user", "content": "Hi"}], business=business, agent_slug='crux')
    
    assert response == "Hello! I am Crux."
    mock_create_agent.assert_called_once()
