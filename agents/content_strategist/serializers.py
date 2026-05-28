from rest_framework import serializers
from .models import ContentPiece, Campaign


class ContentPieceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentPiece
        fields = "__all__"
        read_only_fields = (
            "id", "business", "generated_content",
            "status", "word_count", "created_at", "updated_at",
        )


class CampaignSerializer(serializers.ModelSerializer):
    content_pieces    = ContentPieceSerializer(many=True, read_only=True)
    content_piece_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=ContentPiece.objects.all(),
        source="content_pieces",
        required=False,
    )

    class Meta:
        model = Campaign
        fields = "__all__"
        read_only_fields = ("id", "business", "created_at", "updated_at")
