from rest_framework import serializers
from .models import DocumentationProject, DocPage


class DocPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocPage
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "ai_generated", "word_count")


class DocumentationProjectSerializer(serializers.ModelSerializer):
    pages = DocPageSerializer(many=True, read_only=True)

    class Meta:
        model = DocumentationProject
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "last_generated")
