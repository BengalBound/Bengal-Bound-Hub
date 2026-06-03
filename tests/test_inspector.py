import json
import pytest
from django.urls import reverse
from django.test import override_settings
from unittest.mock import patch
from django.utils import timezone

from hub.models import BusinessInstance
from inspector.models import ComplianceRule, ComplianceCheck, SecurityIncident
from tests.factories import UserFactory, BusinessInstanceFactory, BusinessEmployeeFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def test_setup():
    user = UserFactory()
    biz = BusinessInstanceFactory(owner=user, slug='testbiz')
    employee = BusinessEmployeeFactory(business=biz, user=user, role='ceo')
    
    # Create some compliance rules
    rule_global = ComplianceRule.objects.create(
        name='No Plaintext Secrets',
        category='cybersecurity',
        standard_ref='OWASP-001',
        jurisdiction='*',
        applies_to_agents=['all'],
        rule_description='Do not allow plaintext passwords.',
        is_active=True,
        effective_date=timezone.now().date(),
        review_date=timezone.now().date()
    )
    rule_us = ComplianceRule.objects.create(
        name='PHI Minimization',
        category='privacy',
        standard_ref='HIPAA-001',
        jurisdiction='US',
        applies_to_agents=['all'],
        rule_description='Protected Health Information must be minimized.',
        is_active=True,
        effective_date=timezone.now().date(),
        review_date=timezone.now().date()
    )

    return {
        'user': user,
        'biz': biz,
        'employee': employee,
        'rule_global': rule_global,
        'rule_us': rule_us,
    }


# ── Model Tests ───────────────────────────────────────────────────────────────

def test_compliance_rule_creation(test_setup):
    rule = test_setup['rule_global']
    assert rule.name == 'No Plaintext Secrets'
    assert str(rule) == '[OWASP-001] No Plaintext Secrets'


def test_compliance_check_immutability(test_setup):
    biz = test_setup['biz']
    check = ComplianceCheck.objects.create(
        business=biz,
        agent_name='test-agent',
        client_country='US',
        action_type='test_action',
        action_payload={'key': 'value'},
        decision='approved',
        failed_check='',
        failed_standard='',
        ai_reasoning='OK',
        confidence=1.0
    )
    assert check.log_hash != ''
    assert check.prev_hash == '0' * 64

    # Ensure update raises PermissionError
    with pytest.raises(PermissionError):
        check.decision = 'blocked'
        check.save()

    # Ensure delete raises PermissionError
    with pytest.raises(PermissionError):
        check.delete()


# ── Middleware Tests ──────────────────────────────────────────────────────────

@patch('inspector.views.agent_chat')
def test_middleware_allows_safe_requests(mock_chat, client, test_setup):
    # GET request should bypass middleware completely
    user = test_setup['user']
    biz = test_setup['biz']
    client.force_login(user)

    url = f'/hub/{biz.slug}/settings/'
    response = client.get(url)
    assert response.status_code == 200
    mock_chat.assert_not_called()


@patch('inspector.views.agent_chat')
def test_middleware_blocks_on_violation(mock_chat, client, test_setup):
    user = test_setup['user']
    biz = test_setup['biz']
    client.force_login(user)

    # Mock AI response to block request
    mock_chat.return_value = json.dumps({
        "decision": "blocked",
        "reason": "Request contains plaintext passwords.",
        "failed_check": "cybersecurity",
        "failed_standard": "OWASP-001"
    })

    # A POST request triggers middleware
    url = f'/hub/{biz.slug}/settings/'
    response = client.post(url, {'password': '123'}, content_type='application/json')

    # Expect 403 Forbidden since the request was blocked by Inspector
    assert response.status_code == 403
    assert 'Blocked by Inspector' in response.json()['error']

    # Verify log entry & incident creation
    check = ComplianceCheck.objects.filter(business=biz, decision='blocked').first()
    assert check is not None
    assert check.failed_standard == 'OWASP-001'

    incident = SecurityIncident.objects.get(compliance_check=check)
    assert incident.severity == 'high'
    assert incident.status == 'open'


# ── Views / API Endpoints Tests ───────────────────────────────────────────────

@pytest.mark.urls('bengalbound_core.workspace_urls')
def test_health_check(client, test_setup):
    biz = test_setup['biz']
    url = reverse('inspector:health', kwargs={'slug': biz.slug}, urlconf='bengalbound_core.workspace_urls')
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'


@pytest.mark.urls('bengalbound_core.workspace_urls')
@patch('inspector.views.agent_chat')
def test_check_action_endpoint(mock_chat, client, test_setup):
    user = test_setup['user']
    biz = test_setup['biz']
    client.force_login(user)

    mock_chat.return_value = json.dumps({
        "decision": "approved",
        "reason": "Benign lookup",
        "failed_check": "",
        "failed_standard": ""
    })

    url = reverse('inspector:check-action', kwargs={'slug': biz.slug}, urlconf='bengalbound_core.workspace_urls')
    response = client.post(url, {
        'agent_name': 'Aria',
        'action_type': 'fetch_records',
        'action_payload': {'id': 1},
        'client_country': 'US'
    }, content_type='application/json')

    assert response.status_code == 201
    assert response.json()['decision'] == 'approved'


@pytest.mark.urls('bengalbound_core.workspace_urls')
def test_rules_list(client, test_setup):
    user = test_setup['user']
    biz = test_setup['biz']
    client.force_login(user)

    url = reverse('inspector:rules-list', kwargs={'slug': biz.slug}, urlconf='bengalbound_core.workspace_urls')
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data) >= 2


@pytest.mark.urls('bengalbound_core.workspace_urls')
def test_incidents_management(client, test_setup):
    user = test_setup['user']
    biz = test_setup['biz']
    client.force_login(user)

    # Manually create a check and incident
    check = ComplianceCheck.objects.create(
        business=biz,
        agent_name='Aria',
        client_country='US',
        action_type='process_pii',
        action_payload={'email': 'test@test.com'},
        decision='blocked',
        failed_check='privacy',
        failed_standard='GDPR-001',
        ai_reasoning='Blocked due to GDPR rules',
        confidence=0.98
    )
    incident = SecurityIncident.objects.create(
        compliance_check=check,
        severity='high',
        status='open'
    )

    # 1. List Incidents
    url_list = reverse('inspector:incidents-list', kwargs={'slug': biz.slug}, urlconf='bengalbound_core.workspace_urls')
    response = client.get(url_list)
    assert response.status_code == 200
    assert len(response.data) == 1

    # 2. Resolve Incident
    url_resolve = reverse('inspector:resolve-incident', kwargs={'slug': biz.slug, 'pk': incident.pk}, urlconf='bengalbound_core.workspace_urls')
    response = client.patch(url_resolve, {'resolution_notes': 'Verified consent form exists.'}, content_type='application/json')
    assert response.status_code == 200
    assert response.json()['status'] == 'resolved'
    assert response.json()['resolution_notes'] == 'Verified consent form exists.'


@pytest.mark.urls('bengalbound_core.workspace_urls')
def test_escalation_decision(client, test_setup):
    user = test_setup['user']
    biz = test_setup['biz']
    client.force_login(user)

    check = ComplianceCheck.objects.create(
        business=biz,
        agent_name='Aria',
        client_country='US',
        action_type='mutating_action',
        action_payload={'val': 123},
        decision='escalated',
        failed_check='scope',
        failed_standard='PLAT-002',
        ai_reasoning='Borderline scope limit',
        confidence=0.8
    )
    incident = SecurityIncident.objects.create(
        compliance_check=check,
        severity='medium',
        status='open'
    )

    # 1. Fetch pending escalations
    url_pending = reverse('inspector:escalations-pending', kwargs={'slug': biz.slug}, urlconf='bengalbound_core.workspace_urls')
    response = client.get(url_pending)
    assert response.status_code == 200
    assert len(response.data) == 1

    # 2. Make decision
    url_decide = reverse('inspector:decide-escalation', kwargs={'slug': biz.slug, 'pk': check.pk}, urlconf='bengalbound_core.workspace_urls')
    response = client.post(url_decide, {'decision': 'approved'}, content_type='application/json')
    assert response.status_code == 201
    assert response.json()['decision'] == 'approved'

    # Verify incident was resolved
    incident.refresh_from_db()
    assert incident.status == 'resolved'
    assert 'approved' in incident.resolution_notes


@pytest.mark.urls('bengalbound_core.workspace_urls')
def test_analytics(client, test_setup):
    user = test_setup['user']
    biz = test_setup['biz']
    client.force_login(user)

    ComplianceCheck.objects.create(
        business=biz, agent_name='Aria', client_country='US', action_type='t1',
        action_payload={}, decision='approved', confidence=1.0
    )
    ComplianceCheck.objects.create(
        business=biz, agent_name='Aria', client_country='US', action_type='t2',
        action_payload={}, decision='blocked', failed_check='privacy', confidence=1.0
    )

    url = reverse('inspector:analytics', kwargs={'slug': biz.slug}, urlconf='bengalbound_core.workspace_urls')
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data['total_checks'] == 2
    assert data['blocked_checks'] == 1
    assert data['violation_rate'] == 50.0
