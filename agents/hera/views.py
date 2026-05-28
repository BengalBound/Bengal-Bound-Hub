from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import PolicyQuery, OnboardingTask
from .serializers import PolicyQuerySerializer, OnboardingTaskSerializer

logger = logging.getLogger(__name__)

_HERA_PROMPT = (
    "You are Hera, an expert HR business partner with deep knowledge of employment law, "
    "company policies, and employee wellbeing. Answer the HR question clearly, professionally, "
    "and empathetically. Return only the answer text."
)


class PolicyQueryViewSet(viewsets.ModelViewSet):
    serializer_class = PolicyQuerySerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return PolicyQuery.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business, user=self.request.user)

    @action(detail=True, methods=["post"], url_path="answer")
    def answer(self, request, pk=None):
        """POST /api/v1/hera/queries/<pk>/answer/ — AI answers the HR policy question."""
        query = self.get_object()
        org = request.self._get_business()
        try:
            answer = ai_chat(
                system_prompt=_HERA_PROMPT,
                messages=[{"role": "user", "content": query.question}],
                organization_id=business.id if org else None,
            )
            query.ai_answer = answer
            query.save(update_fields=["ai_answer"])
            AuditLog.objects.create(
                user=request.user, business=business,
                action="hera_answer", resource=f"PolicyQuery/{str(query.id)}",
                status="ALLOWED", inspector_reason="HR policy answer — sub-action audit",
                rules_triggered=[], raw_request_payload={"query_id": str(query.id)},
            )
            return Response(PolicyQuerySerializer(query).data)
        except Exception as exc:
            logger.error("Hera answer failed for query %s: %s", query.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="hera_answer", resource=f"PolicyQuery/{str(query.id)}",
                status="BLOCKED", inspector_reason=f"Answer failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OnboardingTaskViewSet(viewsets.ModelViewSet):
    serializer_class = OnboardingTaskSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return OnboardingTask.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)
