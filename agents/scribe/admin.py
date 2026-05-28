from django.contrib import admin
from agents.scribe.models import Meeting, ActionItem


class ActionItemInline(admin.TabularInline):
    model = ActionItem
    extra = 0
    fields = ['assignee_name', 'task_description', 'is_completed']


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'platform', 'status', 'started_at']
    list_filter = ['status', 'platform']
    search_fields = ['title', 'bot_id']
    inlines = [ActionItemInline]
