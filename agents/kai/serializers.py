from rest_framework import serializers
from .models import Pipeline, Incident


class PipelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pipeline
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "updated_at")


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = "__all__"
        read_only_fields = ("id", "business", "ai_root_cause", "created_at", "updated_at")
