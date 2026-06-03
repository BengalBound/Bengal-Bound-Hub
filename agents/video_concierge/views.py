from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from hub.models import BusinessInstance, BusinessEmployee
from .models import VideoSession
from .serializers import VideoSessionSerializer


class VideoSessionViewSet(viewsets.ModelViewSet):
    serializer_class = VideoSessionSerializer
    queryset = VideoSession.objects.none()
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        return get_object_or_404(BusinessInstance, slug=self.kwargs['slug'])

    def get_queryset(self):
        business = self._get_business()
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user)
        return VideoSession.objects.filter(organization=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(organization=business)
