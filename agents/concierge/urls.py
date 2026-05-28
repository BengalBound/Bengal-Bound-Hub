from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MeetingRequestViewSet, EmailTriageViewSet

app_name = 'concierge'
router = DefaultRouter()
router.register(r"meetings", MeetingRequestViewSet, basename="meeting-request")
router.register(r"emails",   EmailTriageViewSet,    basename="email-triage")

urlpatterns = [path("", include(router.urls))]