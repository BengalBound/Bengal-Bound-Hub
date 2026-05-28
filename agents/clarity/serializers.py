from rest_framework import serializers
from .models import FeedbackSurvey, InsightTheme


class FeedbackSurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackSurvey
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "responses_count")


class InsightThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsightTheme
        fields = "__all__"
        read_only_fields = ("id", "business", "first_seen")
