from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResearchConfigViewSet, ResearchReportViewSet

app_name = 'pulse'
router = DefaultRouter()
router.register(r"configs", ResearchConfigViewSet, basename="research-config")
router.register(r"reports", ResearchReportViewSet, basename="research-report")

urlpatterns = [path("", include(router.urls))]