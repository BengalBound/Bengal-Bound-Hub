from rest_framework import serializers
from .models import Event, Attendee


class AttendeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendee
        fields = "__all__"
        read_only_fields = ("id", "business")


class EventSerializer(serializers.ModelSerializer):
    attendees = AttendeeSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "ai_plan")
