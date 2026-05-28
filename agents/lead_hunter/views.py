import json
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from hub.models import BusinessInstance, BusinessEmployee
from agents.utils import agent_chat
from .models import Prospect, OutreachSequence
from .serializers import ProspectSerializer, OutreachSequenceSerializer

logger = logging.getLogger(__name__)

_SCORE_PROMPT = (
    "You are Lead Hunter, an expert B2B sales intelligence agent. "
    "Evaluate the prospect and return ONLY valid JSON (no markdown): "
    '{"score": <0-100>, "tier": "hot|warm|cold", '
    '"summary": "<2-3 sentence qualification note>", '
    '"next_action": "<recommended outreach step>"}'
)

class ProspectViewSet(viewsets.ModelViewSet):
    serializer_class = ProspectSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Prospect.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="score")
    def score(self, request, slug=None, pk=None):
        """POST /hub/<slug>/agents/lead-hunter/prospects/<pk>/score/ — AI scores the prospect."""
        prospect = self.get_object()
        content = (
            f"Company: {prospect.company_name}\n"
            f"Contact: {prospect.contact_name}\n"
            f"Industry: {prospect.industry}\n"
            f"Notes: {prospect.notes}"
        )
        try:
            raw = agent_chat(
                messages=[
                    {"role": "system", "content": _SCORE_PROMPT},
                    {"role": "user", "content": content}
                ],
                model="gemini/gemini-1.5-flash"
            )
            result = json.loads(raw)
            prospect.score      = int(result.get("score", 0))
            prospect.ai_summary = result.get("summary", "")
            prospect.save(update_fields=["score", "ai_summary"])
            return Response(ProspectSerializer(prospect).data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("Lead Hunter score failed for %s: %s", prospect.id, exc)
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OutreachSequenceViewSet(viewsets.ModelViewSet):
    serializer_class = OutreachSequenceSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return OutreachSequence.objects.filter(business=business)

    def perform_create(self, serializer):
        self._get_business()
        serializer.save()
