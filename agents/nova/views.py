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
from .models import DataSource, DataQuery
from .serializers import DataSourceSerializer, DataQuerySerializer

logger = logging.getLogger(__name__)

_NOVA_PROMPT = (
    "You are Nova, a senior data analyst. Translate the natural language question into SQL "
    "and provide sample insights. Return ONLY valid JSON (no markdown): "
    '{"sql": "<SQL query>", "explanation": "<what the query does>", '
    '"results_preview": [{"column": "value"}]}'
)


class DataSourceViewSet(viewsets.ModelViewSet):
    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return DataSource.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)


class DataQueryViewSet(viewsets.ModelViewSet):
    serializer_class = DataQuerySerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return DataQuery.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="execute")
    def execute(self, request, pk=None):
        """POST /api/v1/nova/queries/<pk>/execute/ — AI translates question to SQL + preview."""
        query = self.get_object()
        org = request.self._get_business()
        try:
            raw = ai_chat(
                system_prompt=_NOVA_PROMPT,
                messages=[{"role": "user", "content": query.question}],
                organization_id=business.id if org else None,
            )
            result = json.loads(raw)
            query.generated_sql   = result.get("sql", "")
            query.results_preview = result.get("results_preview", [])
            query.status          = "completed"
            query.save(update_fields=["generated_sql", "results_preview", "status"])
            AuditLog.objects.create(
                user=request.user, business=business,
                action="nova_execute", resource=f"DataQuery/{str(query.id)}",
                status="ALLOWED", inspector_reason="NL-to-SQL query — sub-action audit",
                rules_triggered=[], raw_request_payload={"query_id": str(query.id)},
            )
            return Response(DataQuerySerializer(query).data)
        except Exception as exc:
            logger.error("Nova execute failed for query %s: %s", query.id, exc)
            query.status = "failed"
            query.save(update_fields=["status"])
            AuditLog.objects.create(
                user=request.user, business=business,
                action="nova_execute", resource=f"DataQuery/{str(query.id)}",
                status="BLOCKED", inspector_reason=f"Query failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
