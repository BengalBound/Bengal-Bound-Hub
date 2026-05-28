from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import Doctor, Appointment
from .serializers import DoctorSerializer, AppointmentSerializer

logger = logging.getLogger(__name__)

_MEDIBOOK_PROMPT = (
    "You are Medibook, an AI medical scheduling assistant. "
    "Write patient preparation instructions and a confirmation message for this appointment. "
    "Be professional, clear, and patient-friendly. Return plain text."
)


class DoctorViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Doctor.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Appointment.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        """POST /api/v1/medibook/appointments/<pk>/confirm/ — AI writes patient notes and confirms."""
        appointment = self.get_object()
        business = self._get_business()
        org = business
        prompt = (
            f"Patient: {appointment.patient_name}\n"
            f"Doctor: {appointment.doctor.name} ({appointment.doctor.specialty})\n"
            f"Scheduled: {appointment.scheduled_at}\n"
            f"Duration: {appointment.duration} min\n"
            f"Reason: {appointment.reason}"
        )
        try:
            notes = ai_chat(
                system_prompt=_MEDIBOOK_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            appointment.ai_notes = notes
            appointment.status = "confirmed"
            appointment.save()
            AuditLog.objects.create(
                user=request.user, business=business,
                action="medibook_confirm_appointment", resource=f"Appointment/{appointment.id}",
                status="ALLOWED", inspector_reason="AI appointment confirmed",
                rules_triggered=[], raw_request_payload={"appointment_id": str(appointment.id)},
            )
            return Response(AppointmentSerializer(appointment).data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("Medibook confirm failed for appointment %s: %s", appointment.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="medibook_confirm_appointment", resource=f"Appointment/{appointment.id}",
                status="BLOCKED", inspector_reason=f"Appointment confirmation failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
