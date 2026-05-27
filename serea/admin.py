from django.contrib import admin
from .models import (
    SereaAgent, AgentInstruction, ConversationMessage, ModerationLog,
    ContentQueue, SereaReport, SocialMediaAccount, ClientContentFile,
    SereaTask, DailyReport, DailyReportItem, CampaignTracker, EngagementLog,
    SereaMemory, CommunityMemberProfile, CustomerServiceThread, EscalationRecord,
)


class AgentInstructionInline(admin.TabularInline):
    model = AgentInstruction
    extra = 1
    fields = ('instruction_text', 'is_active')


@admin.register(SereaAgent)
class SereaAgentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'tier', 'ai_model', 'status', 'tokens_used_this_month', 'effective_token_limit_display', 'created_at')
    list_filter = ('tier', 'status', 'ai_model')
    search_fields = ('tenant__email',)
    inlines = [AgentInstructionInline]
    readonly_fields = ('created_at', 'tokens_used_this_month')

    fieldsets = (
        ('Agent Identity', {
            'fields': ('tenant', 'hired_employee', 'tier', 'persona', 'status'),
        }),
        ('AI Model Configuration', {
            'fields': ('ai_model', 'neurolinkit_api_key', 'groq_api_key', 'openai_api_key', 'openrouter_api_key'),
            'description': (
                'Select the AI model and provide the matching API key. '
                'NeuroLinkIt key → own server models (primary). '
                'Groq key → Groq models. OpenRouter key → any OpenRouter model (incl. free). '
                'Leave blank to fall back to platform-level environment variables.'
            ),
        }),
        ('Platform Management', {
            'fields': ('managed_platforms',),
            'description': (
                'JSON list of platforms this agent actively manages. '
                'Options: "facebook", "instagram", "linkedin". '
                'Example: ["facebook", "instagram", "linkedin"]. '
                'Leave empty to manage all connected platforms.'
            ),
        }),
        ('Token Management', {
            'fields': ('token_limit_override', 'tokens_used_this_month'),
            'description': 'Leave token_limit_override blank to inherit the cap from the hired AI tier.',
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Effective Token Limit')
    def effective_token_limit_display(self, obj):
        if obj.token_limit_override is not None:
            label = '0 (Unlimited)' if obj.token_limit_override == 0 else str(obj.token_limit_override)
            return f"{label} (override)"
        if obj.hired_employee and obj.hired_employee.tier:
            limit = obj.hired_employee.tier.token_limit
            return f"{limit} (from tier)"
        return "—"


@admin.register(AgentInstruction)
class AgentInstructionAdmin(admin.ModelAdmin):
    list_display = ('agent', 'instruction_text', 'is_active', 'created_at')
    list_filter = ('is_active',)


@admin.register(ConversationMessage)
class ConversationMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'agent', 'is_permission_request', 'permission_granted', 'created_at')
    list_filter = ('is_permission_request', 'permission_granted')
    readonly_fields = ('created_at',)


@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    list_display = ('agent', 'platform', 'action_taken', 'confidence_score', 'sentiment_score', 'requires_human', 'created_at')
    list_filter = ('platform', 'action_taken', 'requires_human')
    search_fields = ('comment_text',)
    readonly_fields = ('created_at',)


@admin.register(ContentQueue)
class ContentQueueAdmin(admin.ModelAdmin):
    list_display = ('title', 'agent', 'platform', 'post_date', 'status', 'created_at')
    list_filter = ('status', 'platform')
    readonly_fields = ('created_at',)


@admin.register(SereaReport)
class SereaReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'agent', 'report_type', 'created_at')
    list_filter = ('report_type',)
    search_fields = ('title', 'body')
    readonly_fields = ('created_at',)


@admin.register(SocialMediaAccount)
class SocialMediaAccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'platform', 'agent', 'status', 'is_active', 'connected_at')
    list_filter = ('platform', 'status', 'is_active')
    search_fields = ('account_name', 'account_id')
    readonly_fields = ('connected_at', 'last_synced_at')


@admin.register(ClientContentFile)
class ClientContentFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'agent', 'content_type', 'source_type', 'is_active', 'created_at')
    list_filter = ('content_type', 'source_type', 'is_active')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SereaTask)
class SereaTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'agent', 'status', 'priority', 'due_date', 'created_at')
    list_filter = ('status', 'priority')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')


class DailyReportItemInline(admin.TabularInline):
    model = DailyReportItem
    extra = 0
    fields = ('item_type', 'title', 'outcome', 'is_flagged', 'client_action')
    readonly_fields = ('linked_task',)


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ('agent', 'report_date', 'status', 'flagged_count', 'generated_at')
    list_filter = ('status',)
    readonly_fields = ('generated_at', 'reviewed_at')
    inlines = [DailyReportItemInline]


@admin.register(CampaignTracker)
class CampaignTrackerAdmin(admin.ModelAdmin):
    list_display = ('name', 'agent', 'status', 'start_date', 'end_date', 'platforms_display', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'goal')
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Platforms')
    def platforms_display(self, obj):
        return ', '.join(obj.platforms) if obj.platforms else '—'


@admin.register(EngagementLog)
class EngagementLogAdmin(admin.ModelAdmin):
    list_display = ('agent', 'platform', 'action', 'target_account', 'campaign', 'created_at')
    list_filter = ('platform', 'action')
    search_fields = ('target_account', 'notes')
    readonly_fields = ('created_at',)


@admin.register(SereaMemory)
class SereaMemoryAdmin(admin.ModelAdmin):
    list_display = ('agent', 'memory_type', 'subject', 'importance', 'platform', 'is_active', 'updated_at')
    list_filter = ('memory_type', 'importance', 'is_active')
    search_fields = ('subject', 'content')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_active',)


@admin.register(CommunityMemberProfile)
class CommunityMemberProfileAdmin(admin.ModelAdmin):
    list_display = ('agent', 'platform', 'username', 'engagement_score', 'violation_count', 'is_flagged', 'is_blocked', 'last_seen_at')
    list_filter = ('platform', 'is_flagged', 'is_blocked')
    search_fields = ('username', 'display_name', 'platform_user_id', 'notes')
    readonly_fields = ('first_seen_at', 'last_seen_at')


@admin.register(CustomerServiceThread)
class CustomerServiceThreadAdmin(admin.ModelAdmin):
    list_display = ('agent', 'platform', 'customer_name', 'subject', 'status', 'priority', 'opened_at', 'last_activity_at')
    list_filter = ('status', 'priority', 'platform')
    search_fields = ('customer_name', 'subject', 'serea_notes')
    readonly_fields = ('opened_at', 'last_activity_at', 'resolved_at')


@admin.register(EscalationRecord)
class EscalationRecordAdmin(admin.ModelAdmin):
    list_display = ('agent', 'escalation_type', 'severity', 'platform', 'status', 'escalated_to', 'created_at')
    list_filter = ('escalation_type', 'severity', 'status')
    search_fields = ('description', 'escalated_to')
    readonly_fields = ('created_at', 'resolved_at')
