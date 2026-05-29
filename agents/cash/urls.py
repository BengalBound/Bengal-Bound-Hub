from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, PayrollRunViewSet

app_name = 'cash'
router = DefaultRouter()
router.register(r"employees", EmployeeViewSet, basename="employee")
router.register(r"payroll-runs", PayrollRunViewSet, basename="payroll-run")

urlpatterns = [path("", include(router.urls))]
