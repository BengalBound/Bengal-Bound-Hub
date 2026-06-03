import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from hub.models import BusinessInstance, BusinessEmployee
from agents.utils import agent_chat
from .models import ContentPiece, Campaign
from .serializers import ContentPieceSerializer, CampaignSerializer

logger = logging.getLogger(__name__)

_SEREA_SYSTEM = (
    "You are Serea, a world-class content strategist and copywriter for {business_name}. "
    "Write compelling, on-brand content that achieves the user's stated goal. "
    "Return only the content itself — no meta-commentary."
)


class ContentPieceViewSet(viewsets.ModelViewSet):
    serializer_class = ContentPieceSerializer
    queryset = ContentPiece.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        return ContentPiece.objects.filter(business=self._get_business())

    def perform_create(self, serializer):
        serializer.save(business=self._get_business())

    @action(detail=True, methods=["post"], url_path="generate")
    def generate(self, request, slug=None, pk=None):
        """POST /hub/<slug>/agents/content-strategist/content/<pk>/generate/ — AI generates content."""
        piece = self.get_object()
        business = self._get_business()
        system_prompt = _SEREA_SYSTEM.format(business_name=business.name)
        try:
            content = agent_chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": piece.prompt},
                ],
            )
            piece.generated_content = content
            piece.status = "generated"
            piece.word_count = len(content.split())
            piece.save(update_fields=["generated_content", "status", "word_count"])
            return Response(ContentPieceSerializer(piece).data)
        except Exception as exc:
            logger.error("Serea content generation failed for piece %s: %s", piece.id, exc)
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CampaignViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignSerializer
    queryset = Campaign.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        return Campaign.objects.filter(business=self._get_business())

    def perform_create(self, serializer):
        serializer.save(business=self._get_business())
