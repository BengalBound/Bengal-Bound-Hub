from rest_framework import serializers
from .models import TranslationJob, TranslationOutput


class TranslationOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranslationOutput
        fields = "__all__"
        read_only_fields = ("id", "created_at")


class TranslationJobSerializer(serializers.ModelSerializer):
    outputs = TranslationOutputSerializer(many=True, read_only=True)

    class Meta:
        model = TranslationJob
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "completed_at", "status")
