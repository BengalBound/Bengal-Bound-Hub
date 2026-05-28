"""
voice_receptionist/views.py
------------------------------
DRF ViewSets for the Voice Receptionist API.
All endpoints live under /api/v1/voice/ (wired in urls.py).
"""

import logging
from datetime import timedelta

from django.utils import timezone
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import FirebaseAuthentication
from .permissions import IsFirebaseAdmin, IsFirebaseAdminOrManager, IsFirebaseAuthenticated
from .models import (
    BusinessProfile, Call, Appointment, SpamLog, SpamBlocklist,
    UserProfile, NotificationTemplate,
)
from .serializers import (
    BusinessProfileSerializer,
    CallSerializer,
    AppointmentSerializer,
    AppointmentListSerializer,
    SpamLogSerializer,
    SpamBlocklistSerializer,
    UserProfileSerializer,
    NotificationTemplateSerializer,
    AnalyticsSummarySerializer,
)
from .google_voice import AVAILABLE_VOICES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------

class FirebaseAuthMixin:
    authentication_classes = [FirebaseAuthentication]

    def dispatch(self, request, *args, **kwargs):
        # Strip the hub slug — VR uses its own BusinessProfile, not hub's BusinessInstance
        kwargs.pop("slug", None)
        return super().dispatch(request, *args, **kwargs)

    def _get_business(self):
        try:
            return self.request.user.voice_profile.business
        except AttributeError:
            return None


# ---------------------------------------------------------------------------
# BusinessProfile
# ---------------------------------------------------------------------------

class BusinessProfileViewSet(FirebaseAuthMixin, viewsets.ModelViewSet):
    """
    GET    /api/v1/voice/profile/           — List profiles (admin sees all; others see own)
    GET    /api/v1/voice/profile/{id}/      — Detail
    PUT    /api/v1/voice/profile/{id}/      — Update
    POST   /api/v1/voice/profile/           — Create (admin only)
    DELETE /api/v1/voice/profile/{id}/      — Delete (admin only)
    GET    /api/v1/voice/profile/voices/    — List available TTS voices
    """
    serializer_class = BusinessProfileSerializer

    def get_permissions(self):
        if self.action in ("create", "destroy"):
            return [IsFirebaseAdmin()]
        return [IsFirebaseAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        try:
            profile = user.voice_profile
            if profile.role == "admin":
                return BusinessProfile.objects.all()
            if self._get_business():
                return BusinessProfile.objects.filter(id=self._get_business().id)
        except AttributeError:
            pass
        return BusinessProfile.objects.none()

    @action(detail=False, methods=["get"])
    def voices(self, request):
        """Return list of available Google Cloud TTS voices."""
        return Response(AVAILABLE_VOICES)

    @action(detail=True, methods=["post"])
    def test_hours(self, request, pk=None):
        """Return whether the business is currently open."""
        business = self.get_object()
        return Response({"is_open": business.is_open_now()})


# ---------------------------------------------------------------------------
# Call Log
# ---------------------------------------------------------------------------

class CallViewSet(FirebaseAuthMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    GET  /api/v1/voice/calls/       — Paginated call log
    GET  /api/v1/voice/calls/{id}/  — Call detail with full transcript
    """
    serializer_class = CallSerializer
    permission_classes = [IsFirebaseAdminOrManager]

    def get_queryset(self):
        return self._scoped_calls().order_by("-started_at")

    def _scoped_calls(self):
        try:
            profile = self.request.user.voice_profile
            if profile.role == "admin":
                return Call.objects.select_related("business").all()
            if self._get_business():
                return Call.objects.filter(business=self._get_business()).select_related("business")
        except AttributeError:
            pass
        return Call.objects.none()

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Return calls currently in ongoing status (Live Call Feed)."""
        active = self._scoped_calls().filter(status="ongoing")
        serializer = self.get_serializer(active, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------

class AppointmentViewSet(FirebaseAuthMixin, viewsets.ModelViewSet):
    """
    Full CRUD for /api/v1/voice/appointments/
    POST also triggers calendar sync + notifications.
    """
    permission_classes = [IsFirebaseAdminOrManager]

    def get_serializer_class(self):
        if self.action == "list":
            return AppointmentListSerializer
        return AppointmentSerializer

    def get_queryset(self):
        qs = Appointment.objects.select_related("business", "call")
        try:
            profile = self.request.user.voice_profile
            if profile.role != "admin" and self._get_business():
                qs = qs.filter(business=self._get_business())
        except AttributeError:
            return Appointment.objects.none()

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Filter by date range
        date_from = self.request.query_params.get("from")
        date_to   = self.request.query_params.get("to")
        if date_from:
            qs = qs.filter(scheduled_at__gte=date_from)
        if date_to:
            qs = qs.filter(scheduled_at__lte=date_to)

        return qs.order_by("scheduled_at")

    def perform_create(self, serializer):
        appt = serializer.save()
        # Sync to Google Calendar async-ish (sync in Phase 1 — async queue in Phase 2)
        try:
            from .calendar_sync import create_appointment_event
            event_id = create_appointment_event(appt.business, appt)
            if event_id:
                appt.gcal_event_id = event_id
                appt.calendar_synced = True
                appt.save(update_fields=["gcal_event_id", "calendar_synced"])
        except Exception as e:
            logger.warning("GCal sync skipped on create: %s", e)
        # Notifications
        from .notifications import notify_appointment
        notify_appointment(appt, "booking_confirmed")

    def perform_update(self, serializer):
        appt = serializer.save()
        # Update calendar event
        try:
            from .calendar_sync import update_appointment_event
            update_appointment_event(appt.business, appt)
        except Exception as e:
            logger.warning("GCal sync skipped on update: %s", e)
        from .notifications import notify_appointment
        notify_appointment(appt, "booking_rescheduled")

    def perform_destroy(self, instance):
        try:
            from .calendar_sync import delete_appointment_event
            if instance.gcal_event_id:
                delete_appointment_event(instance.business, instance.gcal_event_id)
        except Exception as e:
            logger.warning("GCal delete skipped: %s", e)
        from .notifications import notify_appointment
        instance.status = "cancelled"
        instance.save(update_fields=["status"])
        notify_appointment(instance, "booking_cancelled")
        # Soft delete — keep the record, just mark cancelled

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """Return appointments in the next 7 days."""
        now = timezone.now()
        qs  = self.get_queryset().filter(
            scheduled_at__gte=now,
            scheduled_at__lte=now + timedelta(days=7),
            status="confirmed",
        )
        serializer = AppointmentListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def available_slots(self, request):
        """
        GET /api/v1/voice/appointments/available_slots/?date=YYYY-MM-DD&duration=60
        Return available time slots for a given date.
        """
        from .calendar_sync import get_available_slots
        from datetime import datetime, time

        date_str  = request.query_params.get("date")
        duration  = int(request.query_params.get("duration", 60))
        try:
            profile  = request.user.voice_profile
            business = self._get_business()
        except AttributeError:
            return Response({"error": "No business profile linked"}, status=400)

        if not date_str:
            return Response({"error": "date parameter required (YYYY-MM-DD)"}, status=400)

        try:
            base = datetime.fromisoformat(date_str)
        except ValueError:
            return Response({"error": "Invalid date format"}, status=400)

        start = timezone.make_aware(base.replace(hour=8,  minute=0))
        end   = timezone.make_aware(base.replace(hour=18, minute=0))
        slots = get_available_slots(business, start, end, duration)
        return Response({"available_slots": [s.isoformat() for s in slots]})


# ---------------------------------------------------------------------------
# Spam Log
# ---------------------------------------------------------------------------

class SpamLogViewSet(FirebaseAuthMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    GET   /api/v1/voice/spam/         — Spam log (paginated)
    PATCH /api/v1/voice/spam/{id}/    — Whitelist or blacklist a number
    """
    serializer_class = SpamLogSerializer
    permission_classes = [IsFirebaseAdmin]

    def get_queryset(self):
        try:
            profile = self.request.user.voice_profile
            if profile.role == "admin":
                return SpamLog.objects.select_related("business").order_by("-detected_at")
            if self._get_business():
                return SpamLog.objects.filter(business=self._get_business()).order_by("-detected_at")
        except AttributeError:
            pass
        return SpamLog.objects.none()

    @action(detail=False, methods=["get", "post"])
    def blocklist(self, request):
        """GET/POST community blocklist entries."""
        if request.method == "POST":
            ser = SpamBlocklistSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(ser.data, status=status.HTTP_201_CREATED)
        entries = SpamBlocklist.objects.order_by("-added_at")
        ser = SpamBlocklistSerializer(entries, many=True)
        return Response(ser.data)


# ---------------------------------------------------------------------------
# User Profile
# ---------------------------------------------------------------------------

class UserProfileViewSet(FirebaseAuthMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                          mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Manage user roles. Admin only for list/update."""
    serializer_class = UserProfileSerializer
    permission_classes = [IsFirebaseAdmin]

    def get_queryset(self):
        return UserProfile.objects.select_related("user", "business").all()

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Return the current user's profile. Any authenticated user can call this."""
        try:
            profile = request.user.voice_profile
            return Response(UserProfileSerializer(profile).data)
        except AttributeError:
            return Response({"detail": "Profile not found."}, status=404)


# ---------------------------------------------------------------------------
# Notification Templates
# ---------------------------------------------------------------------------

class NotificationTemplateViewSet(FirebaseAuthMixin, viewsets.ModelViewSet):
    """CRUD for notification templates. Admin only."""
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsFirebaseAdmin]

    def get_queryset(self):
        try:
            profile = self.request.user.voice_profile
            if profile.role == "admin":
                return NotificationTemplate.objects.select_related("business").all()
            if self._get_business():
                return NotificationTemplate.objects.filter(business=self._get_business())
        except AttributeError:
            pass
        return NotificationTemplate.objects.none()


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

class AnalyticsView(FirebaseAuthMixin, APIView):
    """
    GET /api/v1/voice/analytics/?range=7  (days; default 30)
    Returns aggregated call + appointment metrics.
    """
    permission_classes = [IsFirebaseAdminOrManager]

    def get(self, request):
        from .analytics import build_analytics

        days = int(request.query_params.get("range", 30))
        end_dt   = timezone.now()
        start_dt = end_dt - timedelta(days=days)

        try:
            profile  = request.user.voice_profile
            business = self._get_business()
        except AttributeError:
            return Response({"error": "No business profile linked"}, status=400)

        if not business:
            return Response({"error": "No business profile linked"}, status=400)

        data = build_analytics(business, start_dt, end_dt)
        serializer = AnalyticsSummarySerializer(data)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Calendar OAuth
# ---------------------------------------------------------------------------

class CalendarConnectView(FirebaseAuthMixin, APIView):
    """
    GET  /api/v1/voice/calendar/connect/  — Get OAuth URL to connect Google Calendar
    POST /api/v1/voice/calendar/connect/  — Exchange auth code for token + save encrypted
    """
    permission_classes = [IsFirebaseAdmin]

    def get(self, request):
        """Return the Google OAuth2 authorization URL."""
        from google_auth_oauthlib.flow import Flow
        from django.conf import settings

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id":     settings.GOOGLE_CALENDAR_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CALENDAR_CLIENT_SECRET,
                    "redirect_uris": [settings.GOOGLE_CALENDAR_REDIRECT_URI],
                    "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
                    "token_uri":     "https://oauth2.googleapis.com/token",
                }
            },
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        flow.redirect_uri = settings.GOOGLE_CALENDAR_REDIRECT_URI
        auth_url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true")
        return Response({"auth_url": auth_url})

    def post(self, request):
        """Exchange auth code, encrypt token, save to BusinessProfile."""
        from google_auth_oauthlib.flow import Flow
        from django.conf import settings
        from .calendar_sync import _encrypt_token

        code = request.data.get("code")
        if not code:
            return Response({"error": "auth code required"}, status=400)

        try:
            profile  = request.user.voice_profile
            business = self._get_business()
        except AttributeError:
            return Response({"error": "No business profile"}, status=400)

        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id":     settings.GOOGLE_CALENDAR_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CALENDAR_CLIENT_SECRET,
                        "redirect_uris": [settings.GOOGLE_CALENDAR_REDIRECT_URI],
                        "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
                        "token_uri":     "https://oauth2.googleapis.com/token",
                    }
                },
                scopes=["https://www.googleapis.com/auth/calendar"],
            )
            flow.redirect_uri = settings.GOOGLE_CALENDAR_REDIRECT_URI
            flow.fetch_token(code=code)
            creds = flow.credentials
            token_dict = {
                "token":         creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri":     creds.token_uri,
                "client_id":     creds.client_id,
                "client_secret": creds.client_secret,
                "scopes":        list(creds.scopes),
            }
            business.calendar_token = _encrypt_token(token_dict)
            business.calendar_type  = "google"
            business.save(update_fields=["calendar_token", "calendar_type"])
            return Response({"status": "Google Calendar connected successfully."})
        except Exception as e:
            logger.error("Calendar OAuth exchange failed: %s", e)
            return Response({"error": str(e)}, status=500)
