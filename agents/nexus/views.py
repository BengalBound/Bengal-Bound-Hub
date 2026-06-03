from django.shortcuts import get_object_or_404
from hub.models import BusinessInstance, BusinessEmployee
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agents.utils import ai_chat
from agents.utils import AuditLog
from .models import Course, Enrollment
from .serializers import CourseSerializer, EnrollmentSerializer

logger = logging.getLogger(__name__)

_NEXUS_PROMPT = (
    "You are Nexus, an AI learning management specialist. "
    "Generate course modules for the given course. "
    "Return a JSON array of module objects, each with keys: "
    "'title' (string) and 'summary' (1-2 sentence string)."
)


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    queryset = Course.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Course.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)

    @action(detail=True, methods=["post"], url_path="generate")
    def generate(self, request, pk=None):
        """POST /api/v1/nexus/courses/<pk>/generate/ — AI generates course modules."""
        course = self.get_object()
        business = self._get_business()
        org = business
        prompt = (
            f"Course: {course.title}\n"
            f"Type: {course.course_type}\n"
            f"Description: {course.description}\n"
            f"Duration: {course.duration_hours} hours"
        )
        try:
            raw = ai_chat(
                system_prompt=_NEXUS_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                organization_id=business.id if org else None,
            )
            import json
            modules = json.loads(raw)
            course.modules = modules if isinstance(modules, list) else []
            course.ai_generated = True
            course.save()
            AuditLog.objects.create(
                user=request.user, business=business,
                action="nexus_generate_course", resource=f"Course/{course.id}",
                status="ALLOWED", inspector_reason="AI course modules generated",
                rules_triggered=[], raw_request_payload={"course_id": str(course.id)},
            )
            return Response(CourseSerializer(course).data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error("Nexus generate failed for course %s: %s", course.id, exc)
            AuditLog.objects.create(
                user=request.user, business=business,
                action="nexus_generate_course", resource=f"Course/{course.id}",
                status="BLOCKED", inspector_reason=f"Course generation failed: {str(exc)[:100]}",
                rules_triggered=[], raw_request_payload={"error": str(exc)},
            )
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    queryset = Enrollment.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user, is_active=True)
        return business

    def get_queryset(self):
        business = self._get_business()
        return Enrollment.objects.filter(business=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(business=business)
