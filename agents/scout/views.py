from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import Competitor, CompetitorChange
from .serializers import CompetitorSerializer, CompetitorChangeSerializer

logger = logging.getLogger(__name__)

_SCOUT_PROMPT = (
    "You are Scout, an AI competitive intelligence analyst. "
    "Analyze this competitor and write an insightful ai_analysis about what they might be doing. "
    "Return a JSON object with keys: "
    "'change_type' (one of: pricing, product, hiring, ad, content, pr), "
    "'impact' (one of: low, medium, high), "
    "'description' (string), "
    "'ai_analysis' (2-3 sentence string)."
)


class CompetitorViewSet(viewsets.ModelViewSet):
    serializer_class = CompetitorSerializer
    queryset = Competitor.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Competitor.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="analyze")
    def analyze(self, request, pk=None):
        """POST /api/v1/scout/competitors/<pk>/analyze/ — AI creates a CompetitorChange."""
        competitor = self.get_object()
        business = self._get_business()
        org = business
        prompt = (
            f"Competitor: {competitor.name}\n"
            f"Website: {competitor.website}\n"
            f"Twitter: {competitor.twitter_handle}"
        )
        try:
            raw = ai_chat(
                system_prompt=_SCOUT_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            import json
            data = json.loads(raw)
            change = CompetitorChange.objects.create(
                business=business,
                competitor=competitor,
                change_type=data.get("change_type", "content"),
                impact=data.get("impact", "medium"),
                description=data.get("description", ""),
                ai_analysis=data.get("ai_analysis", ""),
            )
            competitor.last_checked = timezone.now()
            competitor.save()
            AuditLog.objects.create(
                user=request.user, business=business,
                action="scout_analyze_competitor", resource=f"Competitor/{competitor.id}",
                status="ALLOWED", inspector_reason="AI competitor analyzed",
                rules_triggered=[], raw_request_payload={"competitor_id": str(competitor.id)},
            )
            return Response(CompetitorChangeSerializer(change).data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            logger.error("Scout analyze failed for competitor %s: %s", competitor.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="scout_analyze_competitor", resource=f"Competitor/{competitor.id}",
                status="BLOCKED", inspector_reason=f"Competitor analysis failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CompetitorChangeViewSet(viewsets.ModelViewSet):
    serializer_class = CompetitorChangeSerializer
    queryset = CompetitorChange.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return CompetitorChange.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)
