import pytest
from django.utils import timezone
from hub.models import BusinessInstance, BusinessEmployee, BusinessSubscription, UserBusinessMembership, DashboardConfig
from workspace_admin.models import Subscription
from serea.models import SereaAgent

pytestmark = pytest.mark.django_db

def test_business_instance_creation(user_factory):
    user = user_factory()
    biz = BusinessInstance.objects.create(owner=user, name="My Biz", slug="my-biz", industry="Retail")
    assert str(biz) == "My Biz"
    assert biz.owner == user

def test_business_employee_creation(user_factory):
    user = user_factory()
    biz = BusinessInstance.objects.create(owner=user, name="My Biz", slug="my-biz")
    emp = BusinessEmployee.objects.create(
        business=biz, user=user, first_name="John", last_name="Doe",
        email="john@doe.com", role="owner"
    )
    assert str(emp) == "John Doe (john@doe.com)"

def test_user_business_membership(user_factory):
    user = user_factory()
    biz = BusinessInstance.objects.create(owner=user, name="My Biz", slug="my-biz")
    mem = UserBusinessMembership.objects.create(user=user, business=biz, role="admin")
    assert str(mem) == f"{user.email} - My Biz (admin)"

def test_dashboard_config(user_factory):
    user = user_factory()
    biz = BusinessInstance.objects.create(owner=user, name="My Biz", slug="my-biz")
    conf = DashboardConfig.objects.create(business=biz, layout_json={"x": 1})
    assert conf.business == biz
    assert conf.layout_json == {"x": 1}
