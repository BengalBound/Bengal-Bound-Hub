from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import BrandMention, PressRelease
from .serializers import BrandMentionSerializer, PressReleaseSerializer

logger = logging.getLogger(__name__)

_LUMA_PROMPT = (
    "You are Luma, an AI PR and brand manager. "
    "Draft a professional, brand-appropriate response to the following brand mention. "
    "The response should be empathetic, on-brand, and address the sentiment directly. "
    "Return only the response text."
)


class BrandMentionViewSet(viewsets.ModelViewSet):
    serializer_class = BrandMentionSerializer
    queryset = BrandMention.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return BrandMention.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="draft-response")
    def draft_response(self, request, pk=None):
        """POST /api/v1/luma/mentions/<pk>/draft-response/ — AI drafts a response."""
        mention = self.get_object()
        business = self._get_business()
        org = business
        prompt = (
            f"Source: {mention.source}\n"
            f"Title: {mention.title}\n"
            f"Snippet: {mention.snippet}\n"
            f"Sentiment: {mention.sentiment}\n"
            f"Urgency: {mention.urgency}"
        )
        try:
            draft = ai_chat(
                system_prompt=_LUMA_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            mention.response_draft = draft
            mention.save()
            AuditLog.objects.create(
                user=request.user, business=business,
                action="luma_draft_response", resource=f"BrandMention/{mention.id}",
                status="ALLOWED", inspector_reason="AI brand response drafted",
                rules_triggered=[], raw_request_payload={"mention_id": str(mention.id)},
            )
            return Response(BrandMentionSerializer(mention).data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("Luma draft-response failed for mention %s: %s", mention.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="luma_draft_response", resource=f"BrandMention/{mention.id}",
                status="BLOCKED", inspector_reason=f"Response draft failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PressReleaseViewSet(viewsets.ModelViewSet):
    serializer_class = PressReleaseSerializer
    queryset = PressRelease.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return PressRelease.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)
