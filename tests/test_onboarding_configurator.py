import json
import pytest
from django.urls import reverse
from unittest.mock import patch
from hub.models import BusinessInstance, DashboardConfig, TenantModule, ModuleCatalog
from workspace_admin.models import HiredAIEmployee, Subscription, AIEmployeeTier
from agents.models import AgentCatalog
from modules.veritas.models import ClientApplication

pytestmark = pytest.mark.django_db

@pytest.fixture
def base_setup(user_factory):
    user = user_factory()
    # Create required agent catalog entry and tier to allow starter agent activation
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
    AgentCatalog.objects.create(
        name="Merch",
        slug="merch",
        role="Product catalog manager",
        description="Merch agent.",
        system_prompt="Be organized.",
        category="Operations",
        tier_required="intern",
        is_active=True
    )
    
    # Create required module catalog entries
    ModuleCatalog.objects.create(
        module_id="crm",
        name="CRM",
        category="sales",
        is_free=True,
        monthly_price_usd=0.00
    )
    ModuleCatalog.objects.create(
        module_id="invoicing",
        name="Invoicing",
        category="finance",
        is_free=True,
        monthly_price_usd=0.00
    )
    
    tier = AIEmployeeTier.objects.create(
        name="intern",
        description="Free Tier",
        monthly_price_usd=0.00,
        token_limit=100000
    )
    AIEmployeeTier.objects.create(
        name="entry",
        description="Entry Tier",
        monthly_price_usd=10.00,
        token_limit=100000
    )
    return user, agent_cat, tier

def test_kyb_redirect_unapproved_user(client, base_setup):
    user, _, _ = base_setup
    client.force_login(user)
    
    # User has no Veritas app, should redirect to apply
    response = client.get(reverse('console_admin:dashboard'))
    assert response.status_code == 302
    assert 'setup/kyb/' in response.url

    # User has Veritas app but it's pending/under_review
    app = ClientApplication.objects.create(
        user=user,
        company_legal_name="Test Legal Corp",
        registration_number="REG123",
        jurisdiction="BD",
        registered_address="Dhaka",
        director_name="CEO",
        director_email="ceo@test.com",
        director_phone="12345",
        status="under_review"
    )
    response = client.get(reverse('console_admin:dashboard'))
    assert response.status_code == 302
    assert 'setup/kyb/pending/' in response.url

def test_unconfigured_redirect_to_setup(client, base_setup):
    user, _, _ = base_setup
    client.force_login(user)
    
    # Approved KYB
    app = ClientApplication.objects.create(
        user=user,
        company_legal_name="Test Legal Corp",
        registration_number="REG123",
        jurisdiction="BD",
        registered_address="Dhaka",
        director_name="CEO",
        director_email="ceo@test.com",
        director_phone="12345",
        status="approved"
    )

    # Has business but not configured
    biz = BusinessInstance.objects.create(
        owner=user,
        name="My Company",
        slug="my-company",
        business_type="ecommerce"
    )
    
    # Go to dashboard, should redirect to setup
    response = client.get(reverse('console_admin:dashboard'))
    assert response.status_code == 302
    assert 'setup/' in response.url

@patch('hub.dashboard_configurator.agent_chat')
def test_onboarding_interview_checkout(mock_chat, client, base_setup):
    user, _, _ = base_setup
    client.force_login(user)
    
    # Approved KYB
    ClientApplication.objects.create(
        user=user,
        company_legal_name="Test Legal Corp",
        registration_number="REG123",
        jurisdiction="BD",
        registered_address="Dhaka",
        director_name="CEO",
        director_email="ceo@test.com",
        director_phone="12345",
        status="approved"
    )

    # Mock the LLM layout response
    mock_chat.return_value = json.dumps({
        "widgets": [
            {"id": "modules_grid", "title": "Modules", "size": "large", "order": 1},
            {"id": "ai_chat", "title": "AI Employee", "size": "medium", "order": 2},
            {"id": "quick_actions", "title": "Quick Actions", "size": "small", "order": 3}
        ],
        "layout": "standard_grid",
        "primary_color_suggestion": "#F97316"
    })

    # Submit the 6-question wizard answers
    response = client.post(reverse('console_admin:process_onboarding_checkout'), {
        'business_name': 'SuperShop',
        'business_type': 'ecommerce',
        'main_challenge': 'getting_leads',
        'team_size': '2–5',
        'platforms': ['WhatsApp Business', 'Facebook/Instagram'],
        'language': 'English',
        'payment_preference': 'bKash'
    })
    
    assert response.status_code == 302
    
    # Verify BusinessInstance and DashboardConfig
    biz = BusinessInstance.objects.filter(owner=user).first()
    assert biz is not None
    assert biz.name == 'SuperShop'
    
    config = DashboardConfig.objects.filter(business=biz).first()
    assert config is not None
    assert config.is_configured is True
    assert config.currency == 'BDT'  # bKash preference sets currency to BDT
    assert config.primary_color == '#F97316' # theme mapping primary color for ecommerce
    assert "concierge" in config.recommended_agents
    
    # Verify starter agent merch is hired
    assert HiredAIEmployee.objects.filter(employer=user, agent_catalog__slug="merch", is_active=True).exists()

@patch('hub.dashboard_configurator.agent_chat')
def test_onboarding_customized_checkout(mock_chat, client, base_setup):
    user, _, _ = base_setup
    client.force_login(user)
    
    # Create required agent catalog entries
    AgentCatalog.objects.get_or_create(
        slug="lead-hunter",
        defaults={
            "name": "Lead Hunter",
            "role": "Lead hunter",
            "description": "Lead hunter",
            "system_prompt": "Hunt leads.",
            "category": "Sales",
            "tier_required": "entry",
            "is_active": True
        }
    )
    
    # Approved KYB
    ClientApplication.objects.create(
        user=user,
        company_legal_name="Test Legal Corp",
        registration_number="REG123",
        jurisdiction="BD",
        registered_address="Dhaka",
        director_name="CEO",
        director_email="ceo@test.com",
        director_phone="12345",
        status="approved"
    )

    # Mock the LLM layout response
    mock_chat.return_value = json.dumps({
        "widgets": [
            {"id": "modules_grid", "title": "Modules", "size": "large", "order": 1},
            {"id": "ai_chat", "title": "AI Employee", "size": "medium", "order": 2}
        ],
        "layout": "standard_grid",
        "primary_color_suggestion": "#F97316"
    })

    # Submit customized modules and agents
    response = client.post(reverse('console_admin:process_onboarding_checkout'), {
        'business_name': 'CustomShop',
        'business_type': 'ecommerce',
        'main_challenge': 'getting_leads',
        'team_size': '2–5',
        'platforms': ['WhatsApp Business'],
        'language': 'English',
        'payment_preference': 'Stripe',
        'custom_modules': ['crm', 'invoicing'],
        'custom_agents': ['concierge', 'lead-hunter'],
        'agent_tier_concierge': 'intern',
        'agent_tier_lead-hunter': 'entry'
    })
    
    assert response.status_code == 302
    
    biz = BusinessInstance.objects.filter(owner=user).first()
    assert biz is not None
    assert biz.name == 'CustomShop'
    
    # Verify TenantModule contains custom modules
    active_module_ids = list(TenantModule.objects.filter(business=biz, is_active=True).values_list('module__module_id', flat=True))
    assert 'crm' in active_module_ids
    assert 'invoicing' in active_module_ids
    
    # Verify both agents hired with specified tiers
    assert HiredAIEmployee.objects.filter(employer=user, agent_catalog__slug="concierge", tier__name="intern", is_active=True).exists()
    assert HiredAIEmployee.objects.filter(employer=user, agent_catalog__slug="lead-hunter", tier__name="entry", is_active=True).exists()

@patch('hub.dashboard_configurator.agent_chat')
def test_natural_language_modifier(mock_chat, client, base_setup):
    user, _, _ = base_setup
    client.force_login(user)

    # Setup approved business and config
    biz = BusinessInstance.objects.create(owner=user, name="ModifyBiz", slug="modifybiz", business_type="agency")
    config = DashboardConfig.objects.create(
        business=biz,
        is_configured=True,
        layout={
            "widgets": [
                {"id": "modules_grid", "title": "Modules", "size": "large", "order": 1},
                {"id": "quick_actions", "title": "Actions", "size": "small", "order": 2}
            ]
        },
        primary_color="#4F46E5"
    )

    # Mock the LLM modifier response to swap order and change color
    mock_chat.return_value = json.dumps({
        "layout": [
            {"id": "quick_actions", "title": "Actions", "size": "small", "order": 1},
            {"id": "modules_grid", "title": "Modules", "size": "large", "order": 2}
        ],
        "theme": "agency",
        "primary_color": "#1E40AF",
        "message": "Swapped widgets and changed color to blue"
    })

    # AJAX POST request to modify endpoint
    response = client.post(
        reverse('console_admin:modify_dashboard_layout'),
        data=json.dumps({'request': 'Move actions to top and make theme dark blue'}),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data['success'] is True
    
    # Reload and verify model fields updated
    config.refresh_from_db()
    assert config.primary_color == '#1E40AF'
    assert config.layout[0]['id'] == 'quick_actions'  # actions moved to top order


def test_skip_onboarding_and_book_meeting(client, base_setup):
    from booking_calendar.models import Appointment
    from hub.models import BusinessInstance, DashboardConfig
    
    user, _, _ = base_setup
    client.force_login(user)

    url = reverse('console_admin:skip_onboarding_book')
    response = client.post(
        url,
        data=json.dumps({
            'date': '2026-06-10',
            'time': '14:30',
            'notes': 'Looking forward to meeting you!'
        }),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data['success'] is True
    assert 'redirect_url' in res_data
    
    # Assert appointment created
    appt = Appointment.objects.filter(client_email=user.email).first()
    assert appt is not None
    assert appt.service_type == 'bengalbound_demo'
    assert appt.notes == 'Looking forward to meeting you!'
    
    # Assert business created and configured
    biz = BusinessInstance.objects.filter(owner=user).first()
    assert biz is not None
    assert biz.name == f"{user.email.split('@')[0]}'s Workspace"
    
    db_config = DashboardConfig.objects.filter(business=biz).first()
    assert db_config is not None
    assert db_config.is_configured is True


def test_public_negotiator_session(client, base_setup):
    from django.urls import reverse
    from modules.veritas.models import ClientApplication
    
    user, _, _ = base_setup
    client.force_login(user)

    # Setup approved KYB so client doesn't get blocked
    ClientApplication.objects.create(
        user=user,
        company_legal_name="Test Legal Corp",
        registration_number="REG123",
        jurisdiction="BD",
        registered_address="Dhaka",
        director_name="CEO",
        director_email="ceo@test.com",
        director_phone="12345",
        status="approved"
    )
    
    negotiator_url = reverse('public_site:demo_negotiate')
    
    # Perform public negotiator POST to claim offer
    response = client.post(negotiator_url, {
        'business_name': 'Negotiated Biz',
        'business_type': 'ecommerce',
        'custom_modules': ['crm', 'invoicing'],
        'custom_agents': ['concierge'],
        'agent_tier_concierge': 'intern'
    })
    
    assert response.status_code == 302
    assert '/accounts/signup/' in response.url
    
    # Check that session key 'negotiated_package' is populated
    session = client.session
    assert 'negotiated_package' in session
    assert session['negotiated_package']['business_name'] == 'Negotiated Biz'
    
    # Visit hybrid onboarding view
    onboarding_url = reverse('console_admin:hybrid_onboarding')
    onboarding_resp = client.get(onboarding_url)
    
    assert onboarding_resp.status_code == 200
    assert b'Negotiated Biz' in onboarding_resp.content
    assert b'crm' in onboarding_resp.content

