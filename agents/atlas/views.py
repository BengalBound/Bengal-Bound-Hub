from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import ExecTask, MeetingBrief
from .serializers import ExecTaskSerializer, MeetingBriefSerializer

logger = logging.getLogger(__name__)

_ATLAS_PROMPT = (
    "You are Atlas, an AI executive assistant. "
    "Generate concise, actionable talking points and a professional briefing for the meeting. "
    "Return a JSON object with keys 'talking_points' (list of strings) and 'ai_briefing' (string summary)."
)


class ExecTaskViewSet(viewsets.ModelViewSet):
    serializer_class = ExecTaskSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return ExecTask.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)


class MeetingBriefViewSet(viewsets.ModelViewSet):
    serializer_class = MeetingBriefSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return MeetingBrief.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="generate")
    def generate(self, request, pk=None):
        """POST /api/v1/atlas/briefs/<pk>/generate/ — AI generates talking points and briefing."""
        brief = self.get_object()
        business = self._get_business()
        org = business
        prompt = (
            f"Meeting: {brief.meeting_title}\n"
            f"Attendees: {brief.attendees}\n"
            f"Agenda: {brief.agenda}"
        )
        try:
            raw = ai_chat(
                system_prompt=_ATLAS_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            import json
            try:
                data = json.loads(raw)
                brief.talking_points = data.get("talking_points", [])
                brief.ai_briefing = data.get("ai_briefing", raw)
            except (json.JSONDecodeError, AttributeError):
                brief.talking_points = []
                brief.ai_briefing = raw
            brief.save()
            AuditLog.objects.create(
                user=request.user, business=business,
                action="atlas_generate_brief", resource=f"MeetingBrief/{brief.id}",
                status="ALLOWED", inspector_reason="AI meeting brief generated",
                rules_triggered=[], raw_request_payload={"brief_id": str(brief.id)},
            )
            return Response(MeetingBriefSerializer(brief).data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("Atlas generate failed for brief %s: %s", brief.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="atlas_generate_brief", resource=f"MeetingBrief/{brief.id}",
                status="BLOCKED", inspector_reason=f"Brief generation failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
