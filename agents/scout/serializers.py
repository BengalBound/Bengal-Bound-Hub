from rest_framework import serializers
from .models import Competitor, CompetitorChange


class CompetitorChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitorChange
        fields = "__all__"
        read_only_fields = ("id", "business", "detected_at", "ai_analysis")


class CompetitorSerializer(serializers.ModelSerializer):
    changes = CompetitorChangeSerializer(many=True, read_only=True)

    class Meta:
        model = Competitor
        fields = "__all__"
        read_only_fields = ("id", "business", "last_checked")
