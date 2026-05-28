from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportConfigViewSet, ReportViewSet

app_name = 'reporting_bot'
router = DefaultRouter()
router.register(r"configs", ReportConfigViewSet, basename="report-config")
router.register(r"reports", ReportViewSet, basename="report")

urlpatterns = [path("", include(router.urls))]
