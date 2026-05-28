from rest_framework import serializers
from .models import MeetingRequest, EmailTriage


class MeetingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingRequest
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "updated_at")


class EmailTriageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTriage
        fields = "__all__"
        read_only_fields = (
            "id", "business", "category", "priority", "is_processed",
            "created_at", "updated_at",
        )
