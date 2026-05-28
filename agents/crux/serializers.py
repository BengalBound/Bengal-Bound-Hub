from rest_framework import serializers
from .models import Contact, Interaction

class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

class ContactSerializer(serializers.ModelSerializer):
    interactions = InteractionSerializer(many=True, read_only=True)

    class Meta:
        model = Contact
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "updated_at")
