from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import Property, Lead
from .serializers import PropertySerializer, LeadSerializer

logger = logging.getLogger(__name__)

_REALT_PROMPT = (
    "You are Realt, an AI real estate specialist. "
    "Evaluate this lead's intent, budget, and preferences. "
    "Return a JSON object with keys: "
    "'ai_score' (integer 0-100, where 100 = highest conversion likelihood), "
    "'ai_notes' (2-3 sentence string with qualification assessment and next steps)."
)


class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Property.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)


class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Lead.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="qualify")
    def qualify(self, request, pk=None):
        """POST /api/v1/realt/leads/<pk>/qualify/ — AI qualifies the lead."""
        lead = self.get_object()
        org = request.self._get_business()
        prompt = (
            f"Lead: {lead.name}\n"
            f"Intent: {lead.intent}\n"
            f"Budget Max: {lead.budget_max}\n"
            f"Preferred Areas: {lead.preferred_areas}\n"
            f"Bedrooms Needed: {lead.bedrooms_needed}"
        )
        try:
            raw = ai_chat(
                system_prompt=_REALT_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            import json
            data = json.loads(raw)
            lead.ai_score = data.get("ai_score", 50)
            lead.ai_notes = data.get("ai_notes", raw)
            lead.status = "qualified"
            lead.save()
            AuditLog.objects.create(
                user=request.user, business=business,
                action="realt_qualify_lead", resource=f"Lead/{lead.id}",
                status="ALLOWED", inspector_reason="AI lead qualified",
                rules_triggered=[], raw_request_payload={"lead_id": str(lead.id)},
            )
            return Response(LeadSerializer(lead).data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("Realt qualify failed for lead %s: %s", lead.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="realt_qualify_lead", resource=f"Lead/{lead.id}",
                status="BLOCKED", inspector_reason=f"Lead qualification failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
