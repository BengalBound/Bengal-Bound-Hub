import sys
import asyncio
import pytest

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from pytest_factoryboy import register
from tests.factories import UserFactory, BusinessInstanceFactory, BusinessEmployeeFactory, AgentCatalogFactory

register(UserFactory)
register(BusinessInstanceFactory)
register(BusinessEmployeeFactory)
register(AgentCatalogFactory)

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authed_client(api_client, user_factory):
    user = user_factory()
    api_client.force_authenticate(user=user)
    return api_client, user

@pytest.fixture
def agent_setup(user_factory):
    from hub.models import BusinessInstance
    from workspace_admin.models import AIEmployeeTier, HiredAIEmployee
    from serea.models import SereaAgent
    user = user_factory()
    biz = BusinessInstance.objects.create(owner=user, name='Biz', slug='biz')
    tier = AIEmployeeTier.objects.create(name='entry', monthly_price_usd=0)
    hired = HiredAIEmployee.objects.create(employer=user, ai_name='Serea', tier=tier)
    agent = SereaAgent.objects.get(hired_employee=hired)
    agent.status = 'idle'
    agent.save()
    return user, agent
