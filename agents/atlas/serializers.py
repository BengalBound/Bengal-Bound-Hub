from rest_framework import serializers
from .models import ExecTask, MeetingBrief


class ExecTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecTask
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at")


class MeetingBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingBrief
        fields = "__all__"
        read_only_fields = ("id", "business", "generated_at", "talking_points", "ai_briefing")
