import pytest
from django.utils import timezone
from hub.models import BusinessInstance, BusinessEmployee, BusinessSubscription, UserBusinessMembership, DashboardConfig
from workspace_admin.models import Subscription
from serea.models import SereaAgent

pytestmark = pytest.mark.django_db

def test_business_instance_creation(user_factory):
    user = user_factory()
    biz = BusinessInstance.objects.create(owner=user, name="My Biz", slug="my-biz", business_type="shop")
    assert str(biz) == "My Biz (Retail Shop)"
    assert biz.owner == user

def test_business_employee_creation(user_factory):
    user = user_factory()
    biz = BusinessInstance.objects.create(owner=user, name="My Biz", slug="my-biz")
    emp = BusinessEmployee.objects.create(
        business=biz, user=user, name="John Doe",
        email="john@doe.com", role="ceo"
    )
    assert str(emp) == "John Doe (CEO / Chief Executive Officer) @ My Biz"

def test_user_business_membership(user_factory):
    user = user_factory()
    biz = BusinessInstance.objects.create(owner=user, name="My Biz", slug="my-biz")
    mem = UserBusinessMembership.objects.create(user=user, business=biz, role="admin")
    assert str(mem) == f"{user.email} → My Biz (Admin)"

def test_dashboard_config(user_factory):
    user = user_factory()
    biz = BusinessInstance.objects.create(owner=user, name="My Biz", slug="my-biz")
    conf = DashboardConfig.objects.create(business=biz, layout={"x": 1})
    assert conf.business == biz
    assert conf.layout == {"x": 1}
