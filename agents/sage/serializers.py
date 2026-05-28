from rest_framework import serializers
from .models import LegalDocument, Clause


class ClauseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clause
        fields = "__all__"
        read_only_fields = ("id", "business", "plain_english", "risk_level", "risk_score", "negotiation_suggestion")


class LegalDocumentSerializer(serializers.ModelSerializer):
    clauses = ClauseSerializer(many=True, read_only=True)

    class Meta:
        model = LegalDocument
        fields = "__all__"
        read_only_fields = (
            "id", "business", "uploaded_at", "reviewed_at",
            "overall_risk", "risk_label", "executive_summary",
        )
