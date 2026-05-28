from rest_framework import serializers
from .models import VideoSession


class VideoSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoSession
        fields = ['id', 'client_name', 'session_type', 'session_id', 'webrtc_sdp',
                  'started_at', 'ended_at', 'duration_seconds', 'resolution_status',
                  'transcript', 'ai_summary']
        read_only_fields = ['id', 'started_at', 'ai_summary']
