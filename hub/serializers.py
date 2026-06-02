from rest_framework import serializers
from .models import BusinessInstance, BusinessEmployee, HubPlanConfig

class BusinessInstanceSerializer(serializers.ModelSerializer):
    business_type_display = serializers.CharField(source='get_business_type_display', read_only=True)
    storage_percent = serializers.FloatField(read_only=True)
    active_modules = serializers.ListField(child=serializers.CharField(), source='active_module_ids', read_only=True)

    class Meta:
        model = BusinessInstance
        fields = [
            'id', 'name', 'slug', 'business_type', 'business_type_display',
            'installation_type', 'tagline', 'business_email', 'business_phone',
            'business_address', 'storage_used_mb', 'storage_limit_mb',
            'storage_percent', 'is_active', 'is_verified', 'created_at',
            'active_modules'
        ]
        read_only_fields = ['slug', 'storage_used_mb', 'is_verified']

class BusinessEmployeeSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = BusinessEmployee
        fields = [
            'id', 'user_email', 'user_full_name', 'role', 'role_display',
            'is_active', 'joined_at'
        ]

class HubPlanConfigSerializer(serializers.ModelSerializer):
    tier_display = serializers.CharField(source='get_tier_display', read_only=True)
    is_active = serializers.BooleanField(source='is_valid', read_only=True)

    class Meta:
        model = HubPlanConfig
        fields = [
            'id', 'tier', 'tier_display', 'price_monthly', 'price_annual',
            'storage_limit_mb', 'max_users', 'is_active', 'start_date', 'end_date'
        ]
