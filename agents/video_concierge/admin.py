from django.contrib import admin
from agents.video_concierge.models import VideoSession


@admin.register(VideoSession)
class VideoSessionAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'organization', 'session_type', 'resolution_status', 'started_at', 'duration_seconds']
    list_filter = ['session_type', 'resolution_status']
    search_fields = ['client_name', 'session_id']
