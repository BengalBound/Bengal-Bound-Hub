"""
voice_receptionist/urls.py
----------------------------
DRF Router + Twilio webhook URL patterns.
Include in Bengal Bound's main urls.py:
    path('api/v1/voice/', include('voice_receptionist.urls'))
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    BusinessProfileViewSet,
    CallViewSet,
    AppointmentViewSet,
    SpamLogViewSet,
    UserProfileViewSet,
    NotificationTemplateViewSet,
    AnalyticsView,
    CalendarConnectView,
)
from .twilio_handler import (
    handle_inbound,
    handle_gather,
    handle_voicemail,
    handle_transfer_complete,
)

app_name = 'voice_receptionist'
router = DefaultRouter()
router.register(r"profile",       BusinessProfileViewSet,      basename="business-profile")
router.register(r"calls",         CallViewSet,                 basename="call")
router.register(r"appointments",  AppointmentViewSet,          basename="appointment")
router.register(r"spam",          SpamLogViewSet,              basename="spam")
router.register(r"users",         UserProfileViewSet,          basename="user-profile")
router.register(r"templates",     NotificationTemplateViewSet, basename="notification-template")

urlpatterns = [
    # DRF API endpoints
    path("", include(router.urls)),

    # Analytics
    path("analytics/", AnalyticsView.as_view(), name="analytics"),

    # Google Calendar OAuth
    path("calendar/connect/", CalendarConnectView.as_view(), name="calendar-connect"),

    # Twilio Webhooks (no Firebase auth — Twilio signature validation instead)
    path("webhook/inbound/",           handle_inbound,           name="twilio-inbound"),
    path("webhook/gather/",            handle_gather,            name="twilio-gather"),
    path("webhook/voicemail/",         handle_voicemail,         name="twilio-voicemail"),
    path("webhook/transfer-complete/", handle_transfer_complete, name="twilio-transfer-complete"),
]
