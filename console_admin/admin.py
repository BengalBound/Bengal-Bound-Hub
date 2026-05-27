from django.contrib import admin
from .models import WorkspaceProject, AITask, AIChatInteraction, SupportTicket

@admin.register(WorkspaceProject)
class WorkspaceProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'created_at')
    search_fields = ('name', 'client__email')

@admin.register(AITask)
class AITaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'assigned_ai', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'assigned_ai__ai_name')

@admin.register(AIChatInteraction)
class AIChatInteractionAdmin(admin.ModelAdmin):
    list_display = ('client', 'ai_employee', 'is_from_ai', 'timestamp')
    list_filter = ('is_from_ai', 'timestamp')

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('subject', 'client', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('subject', 'client__email')
