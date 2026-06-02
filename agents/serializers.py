from rest_framework import serializers
from .models import AgentCatalog

class AgentCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentCatalog
        fields = [
            'id', 'name', 'slug', 'role', 'description',
            'category', 'tier_required', 'is_active', 'icon'
        ]
        # system_prompt is intentionally omitted for security/IP reasons
