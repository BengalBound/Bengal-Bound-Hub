from rest_framework import serializers
from .models import ClientHealth, SuccessEmail

class SuccessEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuccessEmail
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

class ClientHealthSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientHealth
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "updated_at")
