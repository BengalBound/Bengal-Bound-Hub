from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import Employee, PayrollRun
from .serializers import EmployeeSerializer, PayrollRunSerializer

logger = logging.getLogger(__name__)

_CASH_PROMPT = (
    "You are Cash, an AI payroll specialist. "
    "Write a concise executive summary of this payroll run, highlighting key figures and any anomalies. "
    "Return plain text, 2-4 sentences."
)


class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Employee.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)


class PayrollRunViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollRunSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return PayrollRun.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="calculate")
    def calculate(self, request, pk=None):
        """POST /api/v1/cash/payroll-runs/<pk>/calculate/ — AI writes payroll summary."""
        run = self.get_object()
        org = request.self._get_business()
        prompt = (
            f"Month: {run.month}\n"
            f"Employees: {run.employee_count}\n"
            f"Gross: {run.total_gross}\n"
            f"Net: {run.total_net}\n"
            f"Tax: {run.total_tax}\n"
            f"Status: {run.status}"
        )
        try:
            summary = ai_chat(
                system_prompt=_CASH_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            run.ai_summary = summary
            run.save()
            AuditLog.objects.create(
                user=request.user, business=business,
                action="cash_calculate_payroll", resource=f"PayrollRun/{run.id}",
                status="ALLOWED", inspector_reason="AI payroll summary generated",
                rules_triggered=[], raw_request_payload={"run_id": str(run.id)},
            )
            return Response(PayrollRunSerializer(run).data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("Cash calculate failed for run %s: %s", run.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="cash_calculate_payroll", resource=f"PayrollRun/{run.id}",
                status="BLOCKED", inspector_reason=f"Payroll calculation failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
