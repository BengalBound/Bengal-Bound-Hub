from rest_framework import serializers
from .models import Supplier, PurchaseOrder


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "ai_recommendation")


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "ai_summary")
