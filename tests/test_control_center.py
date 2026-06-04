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
