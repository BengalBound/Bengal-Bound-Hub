import json
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from hub.models import BusinessInstance, BusinessEmployee
from agents.utils import agent_chat
from .models import Contact, Interaction
from .serializers import ContactSerializer, InteractionSerializer

logger = logging.getLogger(__name__)

_CRUX_PROMPT = (
    "You are Crux, an AI CRM specialist. "
    "Evaluate this contact's intent and return a JSON object with keys: "
    "'intent_score' (integer 0-100, where 100 = highest buying intent), "
    "'ai_summary' (2-3 sentence string summarizing the contact's profile and likelihood to convert)."
)

class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Contact.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="score")
    def score(self, request, slug=None, pk=None):
        """POST /hub/<slug>/agents/crux/contacts/<pk>/score/ — AI scores contact intent."""
        contact = self.get_object()
        prompt = (
            f"Contact: {contact.name}\n"
            f"Company: {contact.company}\n"
            f"Pipeline Stage: {contact.pipeline_stage}\n"
            f"Is Cold: {contact.is_cold}\n"
            f"Recent interactions: {list(contact.interactions.values('interaction_type', 'summary', 'sentiment')[:5])}"
        )
        try:
            raw = agent_chat(
                messages=[
                    {"role": "system", "content": _CRUX_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                model="gemini/gemini-1.5-flash"
            )
            data = json.loads(raw)
            contact.intent_score = data.get("intent_score", 50)
            contact.ai_summary = data.get("ai_summary", raw)
            contact.save(update_fields=["intent_score", "ai_summary"])
            return Response(ContactSerializer(contact).data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("Crux score failed for contact %s: %s", contact.id, exc)
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InteractionViewSet(viewsets.ModelViewSet):
    serializer_class = InteractionSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Interaction.objects.filter(business=business)

    def perform_create(self, serializer):
        self._get_business()
        serializer.save()
