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
from .models import DocumentationProject, DocPage
from .serializers import DocumentationProjectSerializer, DocPageSerializer

logger = logging.getLogger(__name__)

_DOX_PROMPT = (
    "You are Dox, an AI documentation specialist. "
    "Generate a comprehensive documentation page draft based on the project details. "
    "Return a JSON object with keys: 'title' (string), 'slug' (url-safe string), "
    "'content' (markdown string), 'section' (string)."
)


class DocumentationProjectViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentationProjectSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return DocumentationProject.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="generate")
    def generate(self, request, pk=None):
        """POST /api/v1/dox/projects/<pk>/generate/ — AI generates a DocPage draft."""
        project = self.get_object()
        business = self._get_business()
        org = business
        prompt = (
            f"Project: {project.name}\n"
            f"Doc Type: {project.doc_type}\n"
            f"Description: {project.description}\n"
            f"Repo: {project.repo_url}"
        )
        try:
            raw = ai_chat(
                system_prompt=_DOX_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            import json
            data = json.loads(raw)
            content = data.get("content", raw)
            page = DocPage.objects.create(
                business=business,
                project=project,
                title=data.get("title", f"{project.name} — {project.doc_type}"),
                slug=data.get("slug", f"{project.name.lower().replace(' ', '-')}-{project.doc_type}"),
                content=content,
                section=data.get("section", ""),
                status="draft",
                ai_generated=True,
                word_count=len(content.split()),
            )
            project.last_generated = timezone.now()
            project.save()
            AuditLog.objects.create(
                user=request.user, business=business,
                action="dox_generate_page", resource=f"DocumentationProject/{project.id}",
                status="ALLOWED", inspector_reason="AI doc page generated",
                rules_triggered=[], raw_request_payload={"project_id": str(project.id)},
            )
            return Response(DocPageSerializer(page).data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            logger.error("Dox generate failed for project %s: %s", project.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="dox_generate_page", resource=f"DocumentationProject/{project.id}",
                status="BLOCKED", inspector_reason=f"Doc generation failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocPageViewSet(viewsets.ModelViewSet):
    serializer_class = DocPageSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return DocPage.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)
