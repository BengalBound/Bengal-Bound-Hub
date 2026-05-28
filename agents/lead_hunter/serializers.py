from rest_framework import serializers
from .models import Prospect, OutreachSequence

class OutreachSequenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutreachSequence
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

class ProspectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prospect
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "updated_at")
