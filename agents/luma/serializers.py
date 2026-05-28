from rest_framework import serializers
from .models import BrandMention, PressRelease


class BrandMentionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandMention
        fields = "__all__"
        read_only_fields = ("id", "business", "detected_at", "ai_summary", "response_draft")


class PressReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PressRelease
        fields = "__all__"
        read_only_fields = ("id", "business", "generated_at")
