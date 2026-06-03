from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import ResearchConfig, ResearchReport
from .serializers import ResearchConfigSerializer, ResearchReportSerializer

logger = logging.getLogger(__name__)

_PULSE_PROMPT = (
    "You are Pulse, an AI market research analyst. "
    "Generate a market research report narrative and key findings based on the config. "
    "Return a JSON object with keys: "
    "'narrative' (string, 3-4 sentences), "
    "'key_findings' (list of strings), "
    "'opportunities' (list of strings), "
    "'threats' (list of strings), "
    "'recommendations' (list of strings)."
)


class ResearchConfigViewSet(viewsets.ModelViewSet):
    serializer_class = ResearchConfigSerializer
    queryset = ResearchConfig.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return ResearchConfig.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="generate-report")
    def generate_report(self, request, pk=None):
        """POST /api/v1/pulse/configs/<pk>/generate-report/ — AI generates a ResearchReport."""
        config = self.get_object()
        business = self._get_business()
        org = business
        prompt = (
            f"Industry: {config.industry}\n"
            f"Keywords: {config.keywords}\n"
            f"Competitors: {config.competitors}\n"
            f"Target Markets: {config.target_markets}"
        )
        try:
            raw = ai_chat(
                system_prompt=_PULSE_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            import json
            from django.utils import timezone
            data = json.loads(raw)
            now = timezone.now()
            report = ResearchReport.objects.create(
                business=business,
                period=now.strftime("%B %Y"),
                narrative=data.get("narrative", ""),
                key_findings=data.get("key_findings", []),
                opportunities=data.get("opportunities", []),
                threats=data.get("threats", []),
                recommendations=data.get("recommendations", []),
            )
            AuditLog.objects.create(
                user=request.user, business=business,
                action="pulse_generate_report", resource=f"ResearchConfig/{config.id}",
                status="ALLOWED", inspector_reason="AI research report generated",
                rules_triggered=[], raw_request_payload={"config_id": str(config.id)},
            )
            return Response(ResearchReportSerializer(report).data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            logger.error("Pulse generate-report failed for config %s: %s", config.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="pulse_generate_report", resource=f"ResearchConfig/{config.id}",
                status="BLOCKED", inspector_reason=f"Report generation failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResearchReportViewSet(viewsets.ModelViewSet):
    serializer_class = ResearchReportSerializer
    queryset = ResearchReport.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return ResearchReport.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)
