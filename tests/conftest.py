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
