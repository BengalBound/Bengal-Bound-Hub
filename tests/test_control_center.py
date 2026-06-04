import pytest
from django.urls import reverse
import json

pytestmark = pytest.mark.django_db

def test_control_center_denies_anonymous(client):
    url = reverse('workspace_admin:control_center')
    response = client.get(url)
    assert response.status_code == 302  # Redirects to login
    assert 'login' in response.url

def test_control_center_denies_client_user(client, user_factory):
    # A standard client user with role='console_user' and is_staff=False
    user = user_factory(role='console_user', is_staff=False, is_superuser=False)
    client.force_login(user)
    
    url = reverse('workspace_admin:control_center')
    response = client.get(url)
    assert response.status_code == 302  # Blocked by workspace_admin_required, redirects to login

def test_control_center_allows_super_admin(client, user_factory):
    # A workspace admin user (e.g. superuser or role='super_admin' + is_staff=True)
    user = user_factory(role='super_admin', is_staff=True, is_superuser=True)
    client.force_login(user)
    
    url = reverse('workspace_admin:control_center')
    response = client.get(url)
    assert response.status_code == 200
    assert b'Executive Command Center' in response.content

def test_control_center_vps_action_api(client, user_factory):
    user = user_factory(role='super_admin', is_staff=True, is_superuser=True)
    client.force_login(user)
    
    # Establish session by visiting the control center first
    url = reverse('workspace_admin:control_center')
    client.get(url)
    
    api_url = reverse('workspace_admin:control_center_vps_action')
    
    # Post restart action
    response = client.post(
        api_url,
        data=json.dumps({'vps_id': 'VPS-01', 'action': 'restart'}),
        content_type='application/json',
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data['success'] is True
    assert res_data['vps_id'] == 'VPS-01'
    assert res_data['vps']['status'] == 'Online'
    assert res_data['vps']['uptime'] == '0h 0m (Just Restarted)'


def test_assign_package_by_workspace_admin(client, user_factory):
    from unittest.mock import patch
    from hub.models import BusinessInstance, TenantModule, ModuleCatalog
    from workspace_admin.models import AIEmployeeTier
    from agents.models import AgentCatalog

    # Create admin user
    admin_user = user_factory(role='super_admin', is_staff=True, is_superuser=True)
    client.force_login(admin_user)
    
    # Create target client user
    client_user = user_factory(role='console_user', is_staff=False, is_superuser=False)
    
    # Setup agent and module
    agent_cat = AgentCatalog.objects.create(
        name="Concierge",
        slug="concierge",
        role="Client Lead Qualifier",
        description="Lead qualifying agent.",
        system_prompt="Be hospitable.",
        category="Operations",
        tier_required="intern",
        is_active=True
    )
    module_cat = ModuleCatalog.objects.create(
        module_id="crm",
        name="CRM",
        category="sales",
        is_free=True,
        monthly_price_usd=0.00
    )
    tier = AIEmployeeTier.objects.create(
        name="intern",
        description="Free Tier",
        monthly_price_usd=0.00,
        token_limit=100000
    )

    url = reverse('workspace_admin:assign_package')
    
    # Verify GET works
    response = client.get(url)
    assert response.status_code == 200
    assert b'Assign Package' in response.content

    # Verify POST works
    # Mocking LiteLLM call during layout generation
    with patch('agents.utils.agent_chat', return_value='["dashboard_pro", "crm"]'):
        post_response = client.post(url, {
            'client_user_id': client_user.id,
            'business_name': 'IT Assigned Company',
            'business_type': 'ecommerce',
            'custom_modules': ['crm'],
            'custom_agents': ['concierge'],
            'agent_tier_concierge': 'intern'
        })
        
    assert post_response.status_code == 302
    
    # Verify business created and assigned to client
    biz = BusinessInstance.objects.filter(owner=client_user).first()
    assert biz is not None
    assert biz.name == 'IT Assigned Company'
    assert biz.business_type == 'ecommerce'
    
    # Verify module provisioned
    assert TenantModule.objects.filter(business=biz, module=module_cat, is_active=True).exists()

