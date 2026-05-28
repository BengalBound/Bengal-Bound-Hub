from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PolicyQueryViewSet, OnboardingTaskViewSet

app_name = 'hera'
router = DefaultRouter()
router.register(r"queries",          PolicyQueryViewSet,   basename="policy-query")
router.register(r"onboarding-tasks", OnboardingTaskViewSet, basename="onboarding-task")

urlpatterns = [path("", include(router.urls))]