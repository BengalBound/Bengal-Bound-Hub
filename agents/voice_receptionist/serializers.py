"""
voice_receptionist/serializers.py
----------------------------------
DRF serializers for all Voice Receptionist models.
"""

from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers
from .models import (
    BusinessProfile,
    Call,
    Appointment,
    SpamLog,
    SpamBlocklist,
    UserProfile,
    NotificationTemplate,
)


# ---------------------------------------------------------------------------
# BusinessProfile
# ---------------------------------------------------------------------------

class BusinessProfileSerializer(serializers.ModelSerializer):
    is_open_now = serializers.SerializerMethodField()
    calendar_token = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model  = BusinessProfile
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def get_is_open_now(self, obj):
        return obj.is_open_now()


class BusinessProfilePublicSerializer(serializers.ModelSerializer):
    """Minimal read-only profile for public/staff endpoints."""
    class Meta:
        model  = BusinessProfile
        fields = ("id", "business_name", "business_type", "agent_name", "services_offered", "business_hours")


# ---------------------------------------------------------------------------
# Call
# ---------------------------------------------------------------------------

class CallSerializer(serializers.ModelSerializer):
    duration_human = serializers.SerializerMethodField()

    class Meta:
        model  = Call
        fields = "__all__"
        read_only_fields = ("id", "transcript", "recording_url", "started_at")

    def get_duration_human(self, obj):
        if obj.duration_seconds is None:
            return None
        m, s = divmod(obj.duration_seconds, 60)
        return f"{m}m {s}s"


# ---------------------------------------------------------------------------
# Appointment
# ---------------------------------------------------------------------------

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Appointment
        fields = "__all__"
        read_only_fields = ("id", "gcal_event_id", "calendar_synced", "created_at", "updated_at")

    def validate_scheduled_at(self, value):
        # Get business min lead time from context if available
        request = self.context.get("request")
        min_hours = 2  # default
        if request and hasattr(request.user, "voice_profile") and request.user.voice_profile.business:
            min_hours = request.user.voice_profile.business.min_lead_time_hours
        min_allowed = timezone.now() + timedelta(hours=min_hours)
        if value < min_allowed:
            raise serializers.ValidationError(
                f"Appointment must be at least {min_hours} hour(s) from now."
            )
        return value


class AppointmentListSerializer(serializers.ModelSerializer):
    """Compact serializer for list views."""
    class Meta:
        model  = Appointment
        fields = (
            "id", "caller_name", "caller_phone", "service_type",
            "scheduled_at", "status", "calendar_synced",
        )


# ---------------------------------------------------------------------------
# SpamLog
# ---------------------------------------------------------------------------

class SpamLogSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SpamLog
        fields = "__all__"
        read_only_fields = ("id", "detected_at")


class SpamBlocklistSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SpamBlocklist
        fields = "__all__"
        read_only_fields = ("id", "added_at")


# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------

class UserProfileSerializer(serializers.ModelSerializer):
    username     = serializers.CharField(source="user.username", read_only=True)
    email        = serializers.EmailField(source="user.email", read_only=True)
    business_name = serializers.CharField(source="business.business_name", read_only=True, default=None)

    class Meta:
        model  = UserProfile
        fields = ("id", "username", "email", "firebase_uid", "role", "business", "business_name", "created_at")
        read_only_fields = ("id", "firebase_uid", "created_at")


# ---------------------------------------------------------------------------
# NotificationTemplate
# ---------------------------------------------------------------------------

class NotificationTemplateSerializer(serializers.ModelSerializer):
    available_variables = serializers.SerializerMethodField()

    class Meta:
        model  = NotificationTemplate
        fields = "__all__"
        read_only_fields = ("id",)

    def get_available_variables(self, obj):
        return [
            "{client_name}", "{appointment_time}", "{service_type}",
            "{business_name}", "{agent_name}", "{appointment_date}",
            "{caller_phone}",
        ]


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

class AnalyticsSummarySerializer(serializers.Serializer):
    total_calls         = serializers.IntegerField()
    completed_calls     = serializers.IntegerField()
    spam_blocked        = serializers.IntegerField()
    transferred_calls   = serializers.IntegerField()
    appointments_booked = serializers.IntegerField()
    booking_rate_pct    = serializers.FloatField()
    spam_rate_pct       = serializers.FloatField()
    avg_duration_seconds = serializers.FloatField(allow_null=True)
    peak_hour           = serializers.IntegerField(allow_null=True)
    top_services        = serializers.ListField(child=serializers.DictField())
    cancellation_rate_pct = serializers.FloatField()
