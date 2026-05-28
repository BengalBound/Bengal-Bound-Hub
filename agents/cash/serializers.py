from rest_framework import serializers
from .models import Employee, PayrollRun


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = "__all__"
        read_only_fields = ("id", "business")


class PayrollRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRun
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "ai_summary")
