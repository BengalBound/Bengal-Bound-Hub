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
from .models import TranslationJob, TranslationOutput
from .serializers import TranslationJobSerializer, TranslationOutputSerializer

logger = logging.getLogger(__name__)

_BABEL_PROMPT = (
    "You are Babel, an AI translation specialist. "
    "Translate the provided text accurately into the target language. "
    "Return only the translated text with no explanations or metadata."
)


class TranslationJobViewSet(viewsets.ModelViewSet):
    serializer_class = TranslationJobSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return TranslationJob.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="translate")
    def translate(self, request, pk=None):
        """POST /api/v1/babel/jobs/<pk>/translate/ — AI translates to all target languages."""
        job = self.get_object()
        business = self._get_business()
        org = business
        try:
            job.status = "processing"
            job.save()
            outputs = []
            for lang in job.target_languages:
                prompt = f"Translate to {lang}:\n\n{job.source_text}"
                translated = ai_chat(
                    system_prompt=_BABEL_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                    organization_id=business.id if org else None,
                )
                output = TranslationOutput.objects.create(
                    job=job, target_language=lang, translated_text=translated,
                )
                outputs.append(output)
            job.status = "completed"
            job.completed_at = timezone.now()
            job.save()
            AuditLog.objects.create(
                user=request.user, business=business,
                action="babel_translate", resource=f"TranslationJob/{job.id}",
                status="ALLOWED", inspector_reason="AI translation completed",
                rules_triggered=[], raw_request_payload={"job_id": str(job.id)},
            )
            return Response(TranslationJobSerializer(job).data, status=status.HTTP_200_OK)
        except Exception as exc:
            job.status = "failed"
            job.save()
            logger.error("Babel translate failed for job %s: %s", job.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="babel_translate", resource=f"TranslationJob/{job.id}",
                status="BLOCKED", inspector_reason=f"Translation failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TranslationOutputViewSet(viewsets.ModelViewSet):
    serializer_class = TranslationOutputSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not getattr(user, "organization_id", None):
            return TranslationOutput.objects.none()
        return TranslationOutput.objects.filter(job__organization=self._get_business())
