import pytest
from django.urls import reverse
from hub.models import (
    BusinessInstance, BusinessEmployee, ModuleCatalog, TenantModule,
    CustomPosition, BusinessSubscription
)

pytestmark = pytest.mark.django_db

def test_hub_landing(client, user_factory):
    user = user_factory()
    client.force_login(user)
    
    url = reverse('hub:hub_landing')
    response = client.get(url)
    assert response.status_code == 200

def test_hub_create(client, user_factory):
    user = user_factory()
    client.force_login(user)
    
    url = reverse('hub:hub_create')
    # GET request
    response = client.get(url)
    assert response.status_code == 200
    
    # POST request
    response = client.post(url, {
        'name': 'Test Business',
        'business_type': 'business',
        'installation_type': 'cloud',
        'tagline': 'We do testing',
        'business_email': 'test@example.com',
        'business_phone': '555-0101'
    })
    
    # Should redirect to onboarding
    assert response.status_code == 302
    assert 'onboarding' in response.url
    
    biz = BusinessInstance.objects.filter(owner=user).first()
    assert biz is not None
    assert biz.name == 'Test Business'
    
    # Assert employee record was created
    assert BusinessEmployee.objects.filter(business=biz, user=user).exists()
    
    # Assert freemium sub was created
    assert BusinessSubscription.objects.filter(business=biz, plan_type='freemium').exists()

def test_hub_dashboard(client, user_factory):
    user = user_factory()
    client.force_login(user)
    
    biz = BusinessInstance.objects.create(owner=user, name='Dashboard Biz', slug='dashboard-biz')
    
    url = reverse('hub:hub_dashboard', kwargs={'slug': biz.slug})
    response = client.get(url)
    
    assert response.status_code == 200
    assert b'Dashboard Biz' in response.content

def test_hub_module_store_and_activation(client, user_factory):
    user = user_factory()
    client.force_login(user)
    
    biz = BusinessInstance.objects.create(owner=user, name='Mod Biz', slug='mod-biz')
    mod = ModuleCatalog.objects.create(module_id='crm', name='CRM', is_available=True)
    
    store_url = reverse('hub:hub_module_store', kwargs={'slug': biz.slug})
    response = client.get(store_url)
    assert response.status_code == 200
    
    activate_url = reverse('hub:hub_activate_module', kwargs={'slug': biz.slug})
    response = client.post(activate_url, {'module_id': 'crm'})
    assert response.status_code == 302
    
    assert TenantModule.objects.filter(business=biz, module=mod, is_active=True).exists()
    
    deactivate_url = reverse('hub:hub_deactivate_module', kwargs={'slug': biz.slug})
    response = client.post(deactivate_url, {'module_id': 'crm'})
    assert response.status_code == 302
    
    assert TenantModule.objects.filter(business=biz, module=mod, is_active=False).exists()

def test_hub_employees(client, user_factory):
    user = user_factory()
    client.force_login(user)
    
    biz = BusinessInstance.objects.create(owner=user, name='Emp Biz', slug='emp-biz')
    
    employees_url = reverse('hub:hub_employees', kwargs={'slug': biz.slug})
    response = client.get(employees_url)
    assert response.status_code == 200
    
    add_url = reverse('hub:hub_add_employee', kwargs={'slug': biz.slug})
    response = client.post(add_url, {
        'name': 'New Employee',
        'email': 'new@emp.com',
        'employee_id': 'EMP001',
        'pin_code': '1234'
    })
    
    assert response.status_code == 302
    assert BusinessEmployee.objects.filter(business=biz, name='New Employee').exists()

def test_hub_settings(client, user_factory):
    user = user_factory()
    client.force_login(user)
    
    biz = BusinessInstance.objects.create(owner=user, name='Set Biz', slug='set-biz')
    
    settings_url = reverse('hub:hub_settings', kwargs={'slug': biz.slug})
    response = client.get(settings_url)
    assert response.status_code == 200
    
    response = client.post(settings_url, {
        'name': 'Updated Biz',
        'tagline': 'A new tagline'
    })
    
    assert response.status_code == 302
    biz.refresh_from_db()
    assert biz.name == 'Updated Biz'
    assert biz.tagline == 'A new tagline'

def test_hub_positions(client, user_factory):
    user = user_factory()
    client.force_login(user)
    
    biz = BusinessInstance.objects.create(owner=user, name='Pos Biz', slug='pos-biz')
    # Assume owner has high access
    BusinessEmployee.objects.create(business=biz, user=user, name='Owner', role='ceo')
    
    url = reverse('hub:hub_positions', kwargs={'slug': biz.slug})
    response = client.get(url)
    assert response.status_code == 200
    
    create_url = reverse('hub:hub_position_create', kwargs={'slug': biz.slug})
    response = client.post(create_url, {
        'name': 'Manager',
        'description': 'Store Manager',
        'access_level': 5,
        'perm_manage_employees': 'on'
    })
    
    assert response.status_code == 302
    assert CustomPosition.objects.filter(business=biz, name='Manager', perm_manage_employees=True).exists()

def test_hub_subscription(client, user_factory):
    user = user_factory()
    client.force_login(user)
    
    biz = BusinessInstance.objects.create(owner=user, name='Sub Biz', slug='sub-biz')
    
    url = reverse('hub:hub_subscription', kwargs={'slug': biz.slug})
    response = client.get(url)
    assert response.status_code == 200
    
    # Change plan
    response = client.post(url, {
        'action': 'change_plan',
        'plan_type': 'standard',
        'billing_cycle': 'monthly'
    })
    
    assert response.status_code == 302
    sub = BusinessSubscription.objects.get(business=biz)
    assert sub.plan_type == 'standard'
