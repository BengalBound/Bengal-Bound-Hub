from rest_framework import serializers
from .models import ComplianceRule, ComplianceCheck, SecurityIncident


class ComplianceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceRule
        fields = '__all__'


class ComplianceCheckSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='business.owner.username', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)

    class Meta:
        model = ComplianceCheck
        fields = '__all__'


class SecurityIncidentSerializer(serializers.ModelSerializer):
    check_details = ComplianceCheckSerializer(source='compliance_check', read_only=True)

    class Meta:
        model = SecurityIncident
        fields = '__all__'
