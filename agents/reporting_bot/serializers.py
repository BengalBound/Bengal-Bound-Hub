from rest_framework import serializers
from .models import ReportConfig, Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = "__all__"
        read_only_fields = ("id", "business", "ai_narrative", "generated_at", "sent_at")


class ReportConfigSerializer(serializers.ModelSerializer):
    reports = ReportSerializer(many=True, read_only=True)

    class Meta:
        model = ReportConfig
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at")
