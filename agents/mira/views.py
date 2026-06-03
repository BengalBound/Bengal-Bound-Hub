import json
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from hub.models import BusinessInstance, BusinessEmployee
from agents.utils import agent_chat
from .models import ClientHealth, SuccessEmail
from .serializers import ClientHealthSerializer, SuccessEmailSerializer

logger = logging.getLogger(__name__)

_MIRA_PROMPT = (
    "You are Mira, an AI customer success manager. "
    "Evaluate the client health metrics and predict churn risk. "
    "Return a JSON object with keys: "
    "'churn_probability' (float 0.0-1.0), "
    "'ai_summary' (2-3 sentence string describing risk level and recommended action)."
)

class ClientHealthViewSet(viewsets.ModelViewSet):
    serializer_class = ClientHealthSerializer
    queryset = ClientHealth.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return ClientHealth.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="predict-churn")
    def predict_churn(self, request, slug=None, pk=None):
        """POST /hub/<slug>/agents/mira/health/<pk>/predict-churn/ — AI predicts churn probability."""
        health = self.get_object()
        prompt = (
            f"Health Score: {health.health_score}\n"
            f"Risk Level: {health.risk_level}\n"
            f"Login Frequency: {health.login_frequency}/week\n"
            f"Feature Usage: {health.feature_usage}%\n"
            f"Open Tickets: {health.open_tickets}"
        )
        try:
            raw = agent_chat(
                messages=[
                    {"role": "system", "content": _MIRA_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                model="gemini/gemini-1.5-flash"
            )
            data = json.loads(raw)
            health.churn_probability = data.get("churn_probability", 0.5)
            health.ai_summary = data.get("ai_summary", raw)
            health.save(update_fields=["churn_probability", "ai_summary"])
            return Response(ClientHealthSerializer(health).data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("Mira predict-churn failed for health %s: %s", health.id, exc)
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SuccessEmailViewSet(viewsets.ModelViewSet):
    serializer_class = SuccessEmailSerializer
    queryset = SuccessEmail.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return SuccessEmail.objects.filter(business=business)

    def perform_create(self, serializer):
        self._get_business()
        serializer.save()
