from rest_framework import serializers
from .models import ITTicket, KnowledgeArticle


class ITTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = ITTicket
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "resolved_at", "ai_solution", "ai_confidence")


class KnowledgeArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeArticle
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "success_count")
