from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from hub.models import BusinessInstance, BusinessEmployee
from .models import VideoPitch
from .serializers import VideoPitchSerializer


class VideoPitchViewSet(viewsets.ModelViewSet):
    serializer_class = VideoPitchSerializer
    queryset = VideoPitch.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        return get_object_or_404(BusinessInstance, slug=self.kwargs['slug'])

    def get_queryset(self):
        business = self._get_business()
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user)
        return VideoPitch.objects.filter(organization=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(organization=business)

    @action(detail=True, methods=['post'])
    def generate(self, request, slug=None, pk=None):
        pitch = self.get_object()
        from agents.pitch_presenter.tasks import generate_video_pitch
        generate_video_pitch.delay(str(pitch.pk))
        return Response({'status': 'queued', 'pitch_id': str(pitch.pk)})
