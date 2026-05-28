from rest_framework import serializers
from .models import Website, SEOIssue


class SEOIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = SEOIssue
        fields = "__all__"
        read_only_fields = ("id", "business", "found_at")


class WebsiteSerializer(serializers.ModelSerializer):
    issues = SEOIssueSerializer(many=True, read_only=True)

    class Meta:
        model = Website
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "last_crawled")
