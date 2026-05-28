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
from .models import ReportConfig, Report
from .serializers import ReportConfigSerializer, ReportSerializer

logger = logging.getLogger(__name__)

_REPORTING_PROMPT = (
    "You are Reporting Bot, an AI business intelligence assistant. "
    "Write a concise executive narrative summarizing the KPIs for this reporting period. "
    "Return plain text, 3-5 sentences highlighting performance and key trends."
)


class ReportConfigViewSet(viewsets.ModelViewSet):
    serializer_class = ReportConfigSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return ReportConfig.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="generate")
    def generate(self, request, pk=None):
        """POST /api/v1/reporting/configs/<pk>/generate/ — AI generates a Report."""
        config = self.get_object()
        business = self._get_business()
        org = business
        now = timezone.now()
        prompt = (
            f"Report: {config.report_name}\n"
            f"Frequency: {config.frequency}\n"
            f"KPIs: {config.kpis}\n"
            f"Data Sources: {config.data_sources}"
        )
        try:
            narrative = ai_chat(
                system_prompt=_REPORTING_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            from datetime import date, timedelta
            today = date.today()
            if config.frequency == "weekly":
                period_start = today - timedelta(days=7)
            elif config.frequency == "biweekly":
                period_start = today - timedelta(days=14)
            else:
                period_start = today.replace(day=1)
            report = Report.objects.create(
                business=business,
                config=config,
                period_start=period_start,
                period_end=today,
                ai_narrative=narrative,
                status="ready",
                generated_at=now,
            )
            AuditLog.objects.create(
                user=request.user, business=business,
                action="reporting_bot_generate", resource=f"ReportConfig/{config.id}",
                status="ALLOWED", inspector_reason="AI report generated",
                rules_triggered=[], raw_request_payload={"config_id": str(config.id)},
            )
            return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            logger.error("Reporting Bot generate failed for config %s: %s", config.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="reporting_bot_generate", resource=f"ReportConfig/{config.id}",
                status="BLOCKED", inspector_reason=f"Report generation failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Report.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)
