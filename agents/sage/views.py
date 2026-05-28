from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import LegalDocument, Clause
from .serializers import LegalDocumentSerializer, ClauseSerializer

logger = logging.getLogger(__name__)

_SAGE_PROMPT = (
    "You are Sage, an AI legal analyst. "
    "Review this legal document and provide analysis. "
    "Return a JSON object with keys: "
    "'executive_summary' (string, 2-3 sentences), "
    "'overall_risk' (integer 0-100), "
    "'risk_label' (one of: low, medium, high, critical), "
    "'clauses' (list of 3 objects, each with keys: clause_number, clause_title, "
    "original_text, plain_english, risk_level (safe/caution/risky/critical), "
    "risk_score (0-100), negotiation_suggestion)."
)


class LegalDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = LegalDocumentSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return LegalDocument.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="review")
    def review(self, request, pk=None):
        """POST /api/v1/sage/documents/<pk>/review/ — AI reviews legal document."""
        doc = self.get_object()
        business = self._get_business()
        org = business
        prompt = (
            f"Document: {doc.name}\n"
            f"Type: {doc.document_type}\n"
            f"Text (first 3000 chars): {doc.raw_text[:3000]}"
        )
        try:
            raw = ai_chat(
                system_prompt=_SAGE_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            import json
            data = json.loads(raw)
            doc.executive_summary = data.get("executive_summary", "")
            doc.overall_risk = data.get("overall_risk", 50)
            doc.risk_label = data.get("risk_label", "medium")
            doc.status = "completed"
            doc.reviewed_at = timezone.now()
            doc.save()
            created_clauses = []
            for c in data.get("clauses", [])[:3]:
                clause = Clause.objects.create(
                    business=business,
                    document=doc,
                    clause_number=c.get("clause_number", ""),
                    clause_title=c.get("clause_title", ""),
                    original_text=c.get("original_text", ""),
                    plain_english=c.get("plain_english", ""),
                    risk_level=c.get("risk_level", "safe"),
                    risk_score=c.get("risk_score", 0),
                    negotiation_suggestion=c.get("negotiation_suggestion", ""),
                )
                created_clauses.append(clause)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="sage_review_document", resource=f"LegalDocument/{doc.id}",
                status="ALLOWED", inspector_reason="AI legal review completed",
                rules_triggered=[], raw_request_payload={"doc_id": str(doc.id)},
            )
            return Response(LegalDocumentSerializer(doc).data, status=status.HTTP_200_OK)
        except Exception as exc:
            doc.status = "failed"
            doc.save()
            logger.error("Sage review failed for doc %s: %s", doc.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="sage_review_document", resource=f"LegalDocument/{doc.id}",
                status="BLOCKED", inspector_reason=f"Legal review failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClauseViewSet(viewsets.ModelViewSet):
    serializer_class = ClauseSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Clause.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)
