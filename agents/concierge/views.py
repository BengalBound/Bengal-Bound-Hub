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
from .models import MeetingRequest, EmailTriage
from .serializers import MeetingRequestSerializer, EmailTriageSerializer

logger = logging.getLogger(__name__)

TRIAGE_SYSTEM_PROMPT = (
    "You are the Concierge email classifier. "
    "Given an email's sender, subject, and body preview, respond with a JSON object containing "
    "exactly two keys: 'category' (one of: inquiry, sales, support, complaint, newsletter, "
    "internal, spam, other) and 'priority' (one of: low, medium, high, urgent). "
    "No markdown fences — raw JSON only."
)


class MeetingRequestViewSet(viewsets.ModelViewSet):
    serializer_class = MeetingRequestSerializer
    queryset = MeetingRequest.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return MeetingRequest.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)


class EmailTriageViewSet(viewsets.ModelViewSet):
    serializer_class = EmailTriageSerializer
    queryset = EmailTriage.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return EmailTriage.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="triage")
    def triage(self, request, pk=None):
        """POST /api/v1/concierge/emails/<pk>/triage/ — AI-classifies category + priority."""
        email = self.get_object()
        business = self._get_business()
        org = business
        messages = [
            {
                "role": "user",
                "content": (
                    f"Sender: {email.sender}\n"
                    f"Subject: {email.subject}\n"
                    f"Body: {email.body_preview}"
                ),
            }
        ]
        try:
            raw = ai_chat(
                system_prompt=TRIAGE_SYSTEM_PROMPT,
                messages=messages,
                organization_id=business.id if org else None
            )
            result = json.loads(raw)
            email.category     = result.get("category", "other")
            email.priority     = result.get("priority", "medium")
            email.is_processed = True
            email.save(update_fields=["category", "priority", "is_processed"])

            # Audit log for sub-action (bypasses middleware)
            AuditLog.objects.create(
                user=request.user,
                business=business,
                action="concierge_triage",
                resource=f"EmailTriage/{email.id}",
                status="ALLOWED",
                inspector_reason="Email classification — sub-action audit",
                rules_triggered=[],
                raw_request_payload={"email_id": str(email.id), "sender": email.sender, "category": email.category},
            )

            return Response(EmailTriageSerializer(email).data)
        except Exception as exc:
            logger.error("Email triage failed for %s: %s", email.id, exc)

            # Audit log for failed triage
            AuditLog.objects.create(
                user=request.user,
                business=business,
                action="concierge_triage",
                resource=f"EmailTriage/{email.id}",
                status="BLOCKED",
                inspector_reason=f"Email triage failed: {str(exc)[:100]}",
                rules_triggered=[],
                raw_request_payload={"error": str(exc)},
            )

            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
