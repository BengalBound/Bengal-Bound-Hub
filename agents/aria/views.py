import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from hub.models import BusinessInstance, BusinessEmployee
from agents.utils import agent_chat
from .models import SupportTicket, TicketResponse
from .serializers import SupportTicketSerializer, TicketResponseSerializer

logger = logging.getLogger(__name__)

_ARIA_PROMPT = (
    "You are Aria, an empathetic and professional customer support specialist. "
    "Draft a clear, helpful, and warm response to the support ticket. "
    "Be solution-focused and concise. Return only the response text — no subject line or metadata."
)

class SupportTicketViewSet(viewsets.ModelViewSet):
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return SupportTicket.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="suggest-response")
    def suggest_response(self, request, slug=None, pk=None):
        """POST /hub/<slug>/agents/aria/tickets/<pk>/suggest-response/ — AI drafts a reply."""
        ticket = self.get_object()
        prompt = f"Subject: {ticket.subject}\nDescription: {ticket.description}"
        try:
            draft = agent_chat(
                messages=[
                    {"role": "system", "content": _ARIA_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                model="gemini/gemini-1.5-flash"
            )
            response_obj = TicketResponse.objects.create(
                ticket=ticket, content=draft, is_ai_generated=True,
            )
            return Response(TicketResponseSerializer(response_obj).data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            logger.error("Aria suggest_response failed for ticket %s: %s", ticket.id, exc)
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TicketResponseViewSet(viewsets.ModelViewSet):
    serializer_class = TicketResponseSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return TicketResponse.objects.filter(ticket__business=business)

    def perform_create(self, serializer):
        self._get_business()
        serializer.save()
