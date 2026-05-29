from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, AttendeeViewSet

app_name = 'tempo'
router = DefaultRouter()
router.register(r"events", EventViewSet, basename="event")
router.register(r"attendees", AttendeeViewSet, basename="attendee")

urlpatterns = [path("", include(router.urls))]
