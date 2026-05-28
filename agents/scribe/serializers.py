from rest_framework import serializers
from .models import Meeting, ActionItem


class ActionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionItem
        fields = ['id', 'assignee_name', 'task_description', 'is_completed', 'extracted_at']
        read_only_fields = ['id', 'extracted_at']


class MeetingSerializer(serializers.ModelSerializer):
    action_items = ActionItemSerializer(many=True, read_only=True)

    class Meta:
        model = Meeting
        fields = ['id', 'title', 'meeting_url', 'bot_id', 'platform',
                  'started_at', 'ended_at', 'raw_transcript', 'executive_summary',
                  'sentiment', 'status', 'action_items', 'created_at']
        read_only_fields = ['id', 'executive_summary', 'sentiment', 'status', 'created_at']
