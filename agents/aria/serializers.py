from rest_framework import serializers
from .models import SupportTicket, TicketResponse

class TicketResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketResponse
        fields = "__all__"
        read_only_fields = ("id", "is_ai_generated", "created_at", "updated_at")

class SupportTicketSerializer(serializers.ModelSerializer):
    responses = TicketResponseSerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "updated_at")
