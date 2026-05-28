from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import Vendor, RFQ
from .serializers import VendorSerializer, RFQSerializer

logger = logging.getLogger(__name__)

_PAYLOAD_PROMPT = (
    "You are Payload, an AI procurement specialist. "
    "Evaluate this RFQ and write a vendor selection recommendation based on the requirements. "
    "Return plain text, 2-4 sentences."
)


class VendorViewSet(viewsets.ModelViewSet):
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Vendor.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)


class RFQViewSet(viewsets.ModelViewSet):
    serializer_class = RFQSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return RFQ.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="evaluate")
    def evaluate(self, request, pk=None):
        """POST /api/v1/payload/rfqs/<pk>/evaluate/ — AI writes vendor recommendation."""
        rfq = self.get_object()
        org = request.self._get_business()
        prompt = (
            f"RFQ Title: {rfq.title}\n"
            f"Description: {rfq.description}\n"
            f"Requirements: {rfq.requirements}\n"
            f"Deadline: {rfq.deadline}"
        )
        try:
            recommendation = ai_chat(
                system_prompt=_PAYLOAD_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            rfq.ai_recommendation = recommendation
            rfq.save()
            AuditLog.objects.create(
                user=request.user, business=business,
                action="payload_evaluate_rfq", resource=f"RFQ/{rfq.id}",
                status="ALLOWED", inspector_reason="AI RFQ evaluated",
                rules_triggered=[], raw_request_payload={"rfq_id": str(rfq.id)},
            )
            return Response(RFQSerializer(rfq).data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("Payload evaluate failed for RFQ %s: %s", rfq.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="payload_evaluate_rfq", resource=f"RFQ/{rfq.id}",
                status="BLOCKED", inspector_reason=f"RFQ evaluation failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
