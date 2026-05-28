from rest_framework import serializers
from .models import Vendor, RFQ


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at")


class RFQSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFQ
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "ai_recommendation")
