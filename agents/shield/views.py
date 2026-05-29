from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import ITTicket, KnowledgeArticle
from .serializers import ITTicketSerializer, KnowledgeArticleSerializer

logger = logging.getLogger(__name__)

_SHIELD_PROMPT = (
    "You are Shield, an AI IT helpdesk specialist. "
    "Diagnose this IT issue and provide a solution. "
    "Return a JSON object with keys: "
    "'ai_solution' (string, step-by-step resolution), "
    "'ai_confidence' (float 0.0-1.0, confidence in the solution)."
)


class ITTicketViewSet(viewsets.ModelViewSet):
    serializer_class = ITTicketSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return ITTicket.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        """POST /api/v1/shield/tickets/<pk>/resolve/ — AI resolves IT ticket."""
        ticket = self.get_object()
        business = self._get_business()
        org = business
        prompt = (
            f"Title: {ticket.title}\n"
            f"Category: {ticket.category}\n"
            f"Priority: {ticket.priority}\n"
            f"Description: {ticket.description}"
        )
        try:
            raw = ai_chat(
                system_prompt=_SHIELD_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            import json
            data = json.loads(raw)
            ticket.ai_solution = data.get("ai_solution", raw)
            ticket.ai_confidence = data.get("ai_confidence", 0.5)
            ticket.status = "ai_resolving"
            ticket.save()
            if ticket.ai_confidence and ticket.ai_confidence > 0.8:
                KnowledgeArticle.objects.create(
                    business=business,
                    title=ticket.title,
                    category=ticket.category,
                    problem=ticket.description,
                    solution=ticket.ai_solution,
                )
            AuditLog.objects.create(
                user=request.user, business=business,
                action="shield_resolve_ticket", resource=f"ITTicket/{ticket.id}",
                status="ALLOWED", inspector_reason="AI IT ticket resolved",
                rules_triggered=[], raw_request_payload={"ticket_id": str(ticket.id)},
            )
            return Response(ITTicketSerializer(ticket).data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("Shield resolve failed for ticket %s: %s", ticket.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="shield_resolve_ticket", resource=f"ITTicket/{ticket.id}",
                status="BLOCKED", inspector_reason=f"Ticket resolution failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KnowledgeArticleViewSet(viewsets.ModelViewSet):
    serializer_class = KnowledgeArticleSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return KnowledgeArticle.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)
