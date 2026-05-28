from rest_framework import serializers
from .models import PolicyQuery, OnboardingTask


class PolicyQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyQuery
        fields = "__all__"
        read_only_fields = ("id", "business", "user", "ai_answer", "created_at", "updated_at")


class OnboardingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingTask
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "updated_at")
