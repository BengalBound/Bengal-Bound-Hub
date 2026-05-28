from rest_framework import serializers
from .models import ContentCalendar, CalendarEntry


class CalendarEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEntry
        fields = "__all__"
        read_only_fields = ("id", "generated_content", "created_at", "updated_at")


class ContentCalendarSerializer(serializers.ModelSerializer):
    entries = CalendarEntrySerializer(many=True, read_only=True)

    class Meta:
        model = ContentCalendar
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "updated_at")
