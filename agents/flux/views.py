from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import Supplier, PurchaseOrder
from .serializers import SupplierSerializer, PurchaseOrderSerializer

logger = logging.getLogger(__name__)

_FLUX_PROMPT = (
    "You are Flux, an AI supply chain specialist. "
    "Analyze the supplier's performance metrics and write a concise ai_summary with a reorder recommendation. "
    "Return plain text, 2-4 sentences."
)


class SupplierViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Supplier.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="forecast")
    def forecast(self, request, pk=None):
        """POST /api/v1/flux/suppliers/<pk>/forecast/ — AI writes supplier summary and reorder recommendation."""
        supplier = self.get_object()
        org = request.self._get_business()
        prompt = (
            f"Supplier: {supplier.name}\n"
            f"Country: {supplier.country}\n"
            f"On-Time Rate: {supplier.on_time_rate}%\n"
            f"Avg Lead Days: {supplier.avg_lead_days}\n"
            f"Rating: {supplier.rating}"
        )
        try:
            summary = ai_chat(
                system_prompt=_FLUX_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            supplier.ai_summary = summary
            supplier.save()
            AuditLog.objects.create(
                user=request.user, business=business,
                action="flux_forecast_supplier", resource=f"Supplier/{supplier.id}",
                status="ALLOWED", inspector_reason="AI supplier forecast generated",
                rules_triggered=[], raw_request_payload={"supplier_id": str(supplier.id)},
            )
            return Response(SupplierSerializer(supplier).data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("Flux forecast failed for supplier %s: %s", supplier.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="flux_forecast_supplier", resource=f"Supplier/{supplier.id}",
                status="BLOCKED", inspector_reason=f"Supplier forecast failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return PurchaseOrder.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)
