from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import Event, Attendee
from .serializers import EventSerializer, AttendeeSerializer

logger = logging.getLogger(__name__)

_TEMPO_PROMPT = (
    "You are Tempo, an AI event management specialist. "
    "Generate a comprehensive event plan including run-of-show, vendor checklist, and timeline. "
    "Return plain text formatted as a professional event brief."
)


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Event.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="plan")
    def plan(self, request, pk=None):
        """POST /api/v1/tempo/events/<pk>/plan/ — AI generates full event plan."""
        event = self.get_object()
        org = request.self._get_business()
        prompt = (
            f"Event: {event.name}\n"
            f"Type: {event.event_type}\n"
            f"Date: {event.date}\n"
            f"Location: {event.location}\n"
            f"Expected Headcount: {event.expected_headcount}\n"
            f"Total Budget: {event.total_budget}\n"
            f"Status: {event.status}"
        )
        try:
            plan = ai_chat(
                system_prompt=_TEMPO_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            event.ai_plan = plan
            event.save()
            AuditLog.objects.create(
                user=request.user, business=business,
                action="tempo_plan_event", resource=f"Event/{event.id}",
                status="ALLOWED", inspector_reason="AI event plan generated",
                rules_triggered=[], raw_request_payload={"event_id": str(event.id)},
            )
            return Response(EventSerializer(event).data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("Tempo plan failed for event %s: %s", event.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="tempo_plan_event", resource=f"Event/{event.id}",
                status="BLOCKED", inspector_reason=f"Event planning failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AttendeeViewSet(viewsets.ModelViewSet):
    serializer_class = AttendeeSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Attendee.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)
