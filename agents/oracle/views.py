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
from .models import Website, SEOIssue
from .serializers import WebsiteSerializer, SEOIssueSerializer

logger = logging.getLogger(__name__)

_ORACLE_PROMPT = (
    "You are Oracle, an AI SEO specialist. "
    "Audit the website and identify 5 SEO issues. "
    "Return a JSON array of 5 objects, each with keys: "
    "'issue_type' (one of: missing_meta, broken_link, duplicate_content, slow_page, missing_schema, mobile_issue, missing_alt), "
    "'severity' (one of: critical, warning, info), "
    "'page_url' (string), 'description' (string), 'fix_suggestion' (string)."
)


class WebsiteViewSet(viewsets.ModelViewSet):
    serializer_class = WebsiteSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Website.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="audit")
    def audit(self, request, pk=None):
        """POST /api/v1/oracle/websites/<pk>/audit/ — AI generates 5 SEOIssues."""
        website = self.get_object()
        business = self._get_business()
        org = business
        prompt = (
            f"Domain: {website.domain}\n"
            f"CMS: {website.cms}"
        )
        try:
            raw = ai_chat(
                system_prompt=_ORACLE_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            import json
            issues_data = json.loads(raw)
            created = []
            for issue in issues_data[:5]:
                seo_issue = SEOIssue.objects.create(
                    business=business,
                    website=website,
                    issue_type=issue.get("issue_type", "missing_meta"),
                    severity=issue.get("severity", "warning"),
                    page_url=issue.get("page_url", website.domain),
                    description=issue.get("description", ""),
                    fix_suggestion=issue.get("fix_suggestion", ""),
                    status="open",
                )
                created.append(seo_issue)
            website.last_crawled = timezone.now()
            website.save()
            AuditLog.objects.create(
                user=request.user, business=business,
                action="oracle_audit_website", resource=f"Website/{website.id}",
                status="ALLOWED", inspector_reason="AI SEO audit completed",
                rules_triggered=[], raw_request_payload={"website_id": str(website.id)},
            )
            return Response(SEOIssueSerializer(created, many=True).data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            logger.error("Oracle audit failed for website %s: %s", website.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="oracle_audit_website", resource=f"Website/{website.id}",
                status="BLOCKED", inspector_reason=f"SEO audit failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SEOIssueViewSet(viewsets.ModelViewSet):
    serializer_class = SEOIssueSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return SEOIssue.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)
