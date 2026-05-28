from rest_framework import serializers
from .models import ResearchConfig, ResearchReport


class ResearchConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchConfig
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at")


class ResearchReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchReport
        fields = "__all__"
        read_only_fields = ("id", "business", "generated_at", "narrative")
