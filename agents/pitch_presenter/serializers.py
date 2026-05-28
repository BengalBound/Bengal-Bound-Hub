from rest_framework import serializers
from .models import VideoPitch, PresentationSlide


class PresentationSlideSerializer(serializers.ModelSerializer):
    class Meta:
        model = PresentationSlide
        fields = ['id', 'slide_number', 'image_url', 'talking_points']


class VideoPitchSerializer(serializers.ModelSerializer):
    slides = PresentationSlideSerializer(many=True, read_only=True)

    class Meta:
        model = VideoPitch
        fields = ['id', 'title', 'business_summary', 'target_audience',
                  'ai_script', 'video_url', 'status', 'avatar_id', 'voice_id',
                  'slides', 'created_at', 'updated_at']
        read_only_fields = ['id', 'ai_script', 'video_url', 'status', 'created_at', 'updated_at']
