from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import json
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import Pipeline, Incident
from .serializers import PipelineSerializer, IncidentSerializer

logger = logging.getLogger(__name__)

_KAI_PROMPT = (
    "You are Kai, a senior DevOps engineer. Analyze the incident and provide a root cause analysis. "
    "Return ONLY valid JSON (no markdown): "
    '{"root_cause": "<string>", "likely_component": "<string>", '
    '"recommended_fix": "<string>", "severity_assessment": "<string>"}'
)


class PipelineViewSet(viewsets.ModelViewSet):
    serializer_class = PipelineSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Pipeline.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)


class IncidentViewSet(viewsets.ModelViewSet):
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Incident.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="analyze")
    def analyze(self, request, pk=None):
        """POST /api/v1/kai/incidents/<pk>/analyze/ — AI performs root cause analysis."""
        incident = self.get_object()
        business = self._get_business()
        org = business
        prompt = f"Title: {incident.title}\nSeverity: {incident.severity}\nDescription: {incident.description}"
        try:
            raw = ai_chat(
                system_prompt=_KAI_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            result = json.loads(raw)
            incident.ai_root_cause = result.get("root_cause", raw)
            incident.status = "investigating"
            incident.save(update_fields=["ai_root_cause", "status"])
            AuditLog.objects.create(
                user=request.user, business=business,
                action="kai_analyze", resource=f"Incident/{str(incident.id)}",
                status="ALLOWED", inspector_reason="Incident root cause analysis — sub-action audit",
                rules_triggered=[], raw_request_payload={"incident_id": str(incident.id)},
            )
            return Response(IncidentSerializer(incident).data)
        except Exception as exc:
            logger.error("Kai analyze failed for incident %s: %s", incident.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="kai_analyze", resource=f"Incident/{str(incident.id)}",
                status="BLOCKED", inspector_reason=f"Analysis failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
