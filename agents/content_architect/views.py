from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import ContentCalendar, CalendarEntry
from .serializers import ContentCalendarSerializer, CalendarEntrySerializer

logger = logging.getLogger(__name__)

_GENERATE_PROMPT = (
    "You are Content Architect, a strategic multi-channel content planner. "
    "Write compelling content for the specified channel based on the brief provided. "
    "Match the channel's native format and voice. Return only the content — no meta-commentary."
)


class ContentCalendarViewSet(viewsets.ModelViewSet):
    serializer_class = ContentCalendarSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return ContentCalendar.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)


class CalendarEntryViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not getattr(user, "organization_id", None):
            return CalendarEntry.objects.none()
        return CalendarEntry.objects.filter(calendar__organization=self._get_business())

    @action(detail=True, methods=["post"], url_path="generate")
    def generate(self, request, pk=None):
        """POST /api/v1/architect/entries/<pk>/generate/ — AI writes content from brief."""
        entry = self.get_object()
        org = request.self._get_business()
        prompt = f"Channel: {entry.channel}\nTitle: {entry.title}\nBrief: {entry.brief}"
        try:
            content = ai_chat(
                system_prompt=_GENERATE_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            entry.generated_content = content
            entry.status = "generated"
            entry.save(update_fields=["generated_content", "status"])
            AuditLog.objects.create(
                user=request.user, business=business,
                action="content_architect_generate", resource=f"CalendarEntry/{str(entry.id)}",
                status="ALLOWED", inspector_reason="Content generation — sub-action audit",
                rules_triggered=[], raw_request_payload={"entry_id": str(entry.id)},
            )
            return Response(CalendarEntrySerializer(entry).data)
        except Exception as exc:
            logger.error("Content generation failed for entry %s: %s", entry.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="content_architect_generate", resource=f"CalendarEntry/{str(entry.id)}",
                status="BLOCKED", inspector_reason=f"Generation failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
