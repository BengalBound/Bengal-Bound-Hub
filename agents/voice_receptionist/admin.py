from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html
from .models import BusinessProfile, Call, Appointment, SpamLog, SpamBlocklist, UserProfile, NotificationTemplate


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display    = ('business_name', 'business_type', 'twilio_phone_number', 'phone', 'agent_name', 'is_active', 'is_open_now')
    list_filter     = ('business_type', 'is_active', 'calendar_type')
    search_fields   = ('business_name', 'twilio_phone_number', 'phone', 'firebase_uid')
    readonly_fields = ('id', 'created_at', 'updated_at', 'webhook_urls')
    fieldsets = (
        ('Business Identity', {
            'fields': ('id', 'firebase_uid', 'business_name', 'business_type', 'is_active'),
        }),
        ('Phone Numbers', {
            'fields': ('phone', 'twilio_phone_number', 'forwarding_number'),
            'description': 'twilio_phone_number must match the number in the Twilio Console webhook.',
        }),
        ('AI Receptionist', {
            'fields': ('agent_name', 'tts_voice', 'language_code', 'greeting_template', 'closing_template'),
        }),
        ('Availability', {
            'fields': ('business_hours', 'min_lead_time_hours', 'buffer_minutes'),
            'description': 'business_hours JSON: {"monday": {"open": "09:00", "close": "17:00"}, ...}',
        }),
        ('Calendar Integration', {
            'fields': ('calendar_type', 'calendar_id', 'calendar_token'),
            'classes': ('collapse',),
        }),
        ('Staff & Services', {
            'fields': ('staff_list', 'services_offered'),
        }),
        ('Twilio Webhook URLs', {
            'fields': ('webhook_urls',),
            'description': 'Paste these into the Twilio Console for this phone number.',
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def webhook_urls(self, obj):
        base = getattr(settings, 'SITE_URL', 'https://yourdomain.com')
        return format_html(
            '<code>Inbound call:</code> {}<br>'
            '<code>Gather (keypress):</code> {}<br>'
            '<code>Voicemail:</code> {}<br>'
            '<code>Transfer complete:</code> {}',
            f'{base}/agents/voice-receptionist/webhook/inbound/',
            f'{base}/agents/voice-receptionist/webhook/gather/',
            f'{base}/agents/voice-receptionist/webhook/voicemail/',
            f'{base}/agents/voice-receptionist/webhook/transfer-complete/',
        )
    webhook_urls.short_description = 'Webhook URLs (paste into Twilio Console)'

    def is_open_now(self, obj):
        return obj.is_open_now()
    is_open_now.boolean = True
    is_open_now.short_description = 'Open now?'


@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display    = ('call_sid', 'business', 'caller_name', 'status', 'duration_seconds', 'escalated_to_human', 'started_at')
    list_filter     = ('status', 'escalated_to_human', 'business')
    search_fields   = ('call_sid', 'caller_name', 'transcript')
    readonly_fields = ('id', 'call_sid', 'raw_twilio_data', 'started_at', 'ended_at')
    ordering        = ('-started_at',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display  = ('caller_name', 'business', 'service_type', 'scheduled_at', 'status', 'caller_phone')
    list_filter   = ('status', 'business')
    search_fields = ('caller_name', 'caller_phone', 'service_type')
    ordering      = ('-scheduled_at',)


@admin.register(SpamLog)
class SpamLogAdmin(admin.ModelAdmin):
    list_display  = ('caller_phone', 'business', 'detection_reason', 'action_taken', 'detected_at')
    list_filter   = ('action_taken', 'business')
    search_fields = ('caller_phone', 'detection_reason')
    ordering      = ('-detected_at',)


@admin.register(SpamBlocklist)
class SpamBlocklistAdmin(admin.ModelAdmin):
    list_display  = ('phone_number', 'source', 'added_at')
    search_fields = ('phone_number',)
    ordering      = ('-added_at',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'firebase_uid', 'role', 'business')
    list_filter   = ('role',)
    search_fields = ('firebase_uid', 'user__email', 'user__username')


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display  = ('business', 'trigger_type', 'is_active')
    list_filter   = ('trigger_type', 'is_active')
    search_fields = ('business__business_name',)
