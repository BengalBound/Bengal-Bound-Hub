from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from hub.models import BusinessInstance, BusinessEmployee
from .models import Meeting
from .serializers import MeetingSerializer


class MeetingViewSet(viewsets.ModelViewSet):
    serializer_class = MeetingSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        return get_object_or_404(BusinessInstance, slug=self.kwargs['slug'])

    def get_queryset(self):
        business = self._get_business()
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user)
        return Meeting.objects.filter(organization=business)

    def perform_create(self, serializer):
        business = self._get_business()
        serializer.save(organization=business)

    @action(detail=True, methods=['post'])
    def process(self, request, slug=None, pk=None):
        meeting = self.get_object()
        from agents.scribe.tasks import process_meeting_notes
        process_meeting_notes.delay(str(meeting.pk))
        return Response({'status': 'queued', 'meeting_id': str(meeting.pk)})
