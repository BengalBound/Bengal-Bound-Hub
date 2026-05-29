from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeedbackSurveyViewSet, InsightThemeViewSet

app_name = 'clarity'
router = DefaultRouter()
router.register(r"surveys", FeedbackSurveyViewSet, basename="feedback-survey")
router.register(r"themes", InsightThemeViewSet, basename="insight-theme")

urlpatterns = [path("", include(router.urls))]
