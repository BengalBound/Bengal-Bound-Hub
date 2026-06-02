from django.contrib import admin
from .models import TwilioConfig, CallQueue, IVRMenu, IVROption, CallLog, AgentCallStatus

@admin.register(TwilioConfig)
class TwilioConfigAdmin(admin.ModelAdmin):
    list_display = ['business', 'account_sid_display', 'default_from_number', 'is_active']
    def account_sid_display(self, obj):
        return f"{obj.account_sid[:8]}..." if obj.account_sid else '—'
    account_sid_display.short_description = 'Account SID'

@admin.register(CallQueue)
class CallQueueAdmin(admin.ModelAdmin):
    list_display = ['name', 'business', 'phone_number', 'strategy', 'is_active']
    list_filter = ['strategy', 'is_active']

@admin.register(IVRMenu)
class IVRMenuAdmin(admin.ModelAdmin):
    list_display = ['name', 'business', 'is_active']
    inlines = []

@admin.register(IVROption)
class IVROptionAdmin(admin.ModelAdmin):
    list_display = ['menu', 'digit', 'label', 'action']

@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ['caller_number', 'called_number', 'direction', 'status', 'agent', 'duration_seconds', 'started_at']
    list_filter = ['direction', 'status']
    search_fields = ['caller_number', 'called_number', 'twilio_call_sid']

@admin.register(AgentCallStatus)
class AgentCallStatusAdmin(admin.ModelAdmin):
    list_display = ['agent', 'business', 'status', 'last_status_change']
    list_filter = ['status']
