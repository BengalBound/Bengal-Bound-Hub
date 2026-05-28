from rest_framework import serializers
from .models import Property, Lead


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = "__all__"
        read_only_fields = ("id", "business", "listed_at", "ai_description")


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "ai_score", "ai_notes")
