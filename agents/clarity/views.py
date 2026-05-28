from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import FeedbackSurvey, InsightTheme
from .serializers import FeedbackSurveySerializer, InsightThemeSerializer

logger = logging.getLogger(__name__)

_CLARITY_PROMPT = (
    "You are Clarity, an AI feedback analyst. "
    "Analyze the feedback survey and identify the top 3 insight themes. "
    "Return a JSON array of 3 objects, each with keys: "
    "'theme' (string), 'theme_type' (one of: pain_point, feature_request, praise, confusion), "
    "'mention_count' (int), 'priority_score' (int 1-100), "
    "'example_quotes' (list of 1-2 short strings), 'ai_analysis' (1-2 sentence string)."
)


class FeedbackSurveyViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackSurveySerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return FeedbackSurvey.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="analyze")
    def analyze(self, request, pk=None):
        """POST /api/v1/clarity/surveys/<pk>/analyze/ — AI generates InsightThemes."""
        survey = self.get_object()
        business = self._get_business()
        org = business
        prompt = (
            f"Survey: {survey.name} (type: {survey.survey_type})\n"
            f"Questions: {survey.questions}\n"
            f"Responses collected: {survey.responses_count}"
        )
        try:
            raw = ai_chat(
                system_prompt=_CLARITY_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            import json
            themes_data = json.loads(raw)
            created = []
            for t in themes_data[:3]:
                theme = InsightTheme.objects.create(
                    business=business,
                    theme=t.get("theme", "Unknown"),
                    theme_type=t.get("theme_type", "pain_point"),
                    mention_count=t.get("mention_count", 1),
                    priority_score=t.get("priority_score"),
                    example_quotes=t.get("example_quotes", []),
                    ai_analysis=t.get("ai_analysis", ""),
                )
                created.append(theme)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="clarity_analyze_survey", resource=f"FeedbackSurvey/{survey.id}",
                status="ALLOWED", inspector_reason="AI insight themes generated",
                rules_triggered=[], raw_request_payload={"survey_id": str(survey.id)},
            )
            return Response(InsightThemeSerializer(created, many=True).data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            logger.error("Clarity analyze failed for survey %s: %s", survey.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="clarity_analyze_survey", resource=f"FeedbackSurvey/{survey.id}",
                status="BLOCKED", inspector_reason=f"Survey analysis failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InsightThemeViewSet(viewsets.ModelViewSet):
    serializer_class = InsightThemeSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return InsightTheme.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)
