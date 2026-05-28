"""
voice_receptionist/admin.py
-----------------------------
Django Admin extensions for all Voice Receptionist models.
Accessible at /admin/ → Voice Receptionist section.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    BusinessProfile,
    Call,
    Appointment,
    SpamLog,
    SpamBlocklist,
    UserProfile,
    NotificationTemplate,
)


# ---------------------------------------------------------------------------
# Inline Admins
# ---------------------------------------------------------------------------

class NotificationTemplateInline(admin.TabularInline):
    model = NotificationTemplate
    extra = 0
    fields = ("trigger_type", "sms_template", "email_subject", "is_active")
    show_change_link = True


class AppointmentInline(admin.TabularInline):
    model = Appointment
    extra = 0
    fields = ("caller_name", "service_type", "scheduled_at", "status", "calendar_synced")
    readonly_fields = ("calendar_synced",)
    show_change_link = True


# ---------------------------------------------------------------------------
# BusinessProfile Admin
# ---------------------------------------------------------------------------

@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display  = ("business_name", "business_type", "phone", "calendar_status", "is_active", "created_at")
    list_filter   = ("business_type", "calendar_type", "is_active")
    search_fields = ("business_name", "phone", "firebase_uid")
    readonly_fields = ("id", "created_at", "updated_at", "calendar_status_detail")
    inlines       = [NotificationTemplateInline]
    fieldsets     = (
        ("Business Info", {
            "fields": ("business_name", "business_type", "phone", "forwarding_number", "twilio_phone_number", "is_active")
        }),
        ("AI Agent Config", {
            "fields": ("agent_name", "tts_voice", "greeting_template", "closing_template", "services_offered", "staff_list")
        }),
        ("Booking Rules", {
            "fields": ("business_hours", "min_lead_time_hours", "buffer_minutes")
        }),
        ("Calendar", {
            "fields": ("calendar_type", "calendar_id", "calendar_status_detail"),
            "description": "OAuth token is stored encrypted and not displayed here."
        }),
        ("Auth", {
            "fields": ("firebase_uid",)
        }),
        ("Timestamps", {
            "fields": ("id", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def calendar_status(self, obj):
        if obj.calendar_token:
            return format_html('<span style="color:green;">✓ Connected ({})</span>', obj.get_calendar_type_display())
        return format_html('<span style="color:red;">✗ Not Connected</span>')
    calendar_status.short_description = "Calendar"

    def calendar_status_detail(self, obj):
        if obj.calendar_token:
            return format_html(
                '<span style="color:green;">✓ {} calendar connected</span>',
                obj.get_calendar_type_display()
            )
        return "No calendar connected. Use /api/v1/voice/calendar/connect/ to link."
    calendar_status_detail.short_description = "Calendar Status"


# ---------------------------------------------------------------------------
# Call Admin
# ---------------------------------------------------------------------------

@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display  = ("caller_phone", "caller_name", "business", "status_badge", "duration_display", "started_at")
    list_filter   = ("status", "is_after_hours", "escalated_to_human", "business")
    search_fields = ("caller_phone", "caller_name", "call_sid", "transcript")
    readonly_fields = ("id", "call_sid", "transcript", "recording_link", "started_at", "ended_at", "raw_twilio_data")
    date_hierarchy = "started_at"
    ordering = ("-started_at",)
    fieldsets = (
        ("Call Info", {
            "fields": ("business", "call_sid", "caller_phone", "caller_name", "status", "started_at", "ended_at")
        }),
        ("Flags", {
            "fields": ("is_after_hours", "escalated_to_human")
        }),
        ("Transcript & Recording", {
            "fields": ("transcript", "recording_link"),
            "classes": ("collapse",)
        }),
        ("Raw Data", {
            "fields": ("raw_twilio_data",),
            "classes": ("collapse",)
        }),
    )

    def status_badge(self, obj):
        colors = {
            "ongoing":     "#2196F3",
            "completed":   "#4CAF50",
            "spam":        "#F44336",
            "transferred": "#FF9800",
            "missed":      "#9E9E9E",
            "voicemail":   "#9C27B0",
        }
        color = colors.get(obj.status, "#9E9E9E")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def duration_display(self, obj):
        if obj.duration_seconds is None:
            return "—"
        m, s = divmod(obj.duration_seconds, 60)
        return f"{m}m {s}s"
    duration_display.short_description = "Duration"

    def recording_link(self, obj):
        if obj.recording_url:
            return format_html('<a href="{}" target="_blank">▶ Play Recording</a>', obj.recording_url)
        return "No recording"
    recording_link.short_description = "Recording"


# ---------------------------------------------------------------------------
# Appointment Admin
# ---------------------------------------------------------------------------

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display  = ("caller_name", "service_type", "scheduled_at", "status_badge", "calendar_synced", "business")
    list_filter   = ("status", "calendar_synced", "is_recurring", "business")
    search_fields = ("caller_name", "caller_phone", "service_type", "notes")
    readonly_fields = ("id", "gcal_event_id", "calendar_synced", "created_at", "updated_at")
    date_hierarchy = "scheduled_at"
    ordering   = ("scheduled_at",)
    actions    = ["mark_cancelled", "sync_to_calendar"]
    fieldsets  = (
        ("Caller Info", {
            "fields": ("caller_name", "caller_phone", "caller_email")
        }),
        ("Appointment", {
            "fields": ("business", "call", "service_type", "scheduled_at", "status")
        }),
        ("Business-Type Fields", {
            "fields": ("address", "insurance_type", "preferred_staff", "notes"),
            "classes": ("collapse",)
        }),
        ("Recurring", {
            "fields": ("is_recurring", "recur_interval_weeks", "parent_appointment"),
            "classes": ("collapse",)
        }),
        ("Calendar", {
            "fields": ("gcal_event_id", "calendar_synced"),
        }),
        ("Timestamps", {
            "fields": ("id", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def status_badge(self, obj):
        colors = {
            "confirmed":   "#4CAF50",
            "cancelled":   "#F44336",
            "rescheduled": "#FF9800",
            "pending":     "#2196F3",
            "completed":   "#9E9E9E",
        }
        color = colors.get(obj.status, "#9E9E9E")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    @admin.action(description="Mark selected appointments as cancelled")
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status="cancelled")
        self.message_user(request, f"{updated} appointment(s) marked as cancelled.")

    @admin.action(description="Sync selected appointments to Google Calendar")
    def sync_to_calendar(self, request, queryset):
        from .calendar_sync import create_appointment_event
        synced = 0
        for appt in queryset:
            try:
                event_id = create_appointment_event(appt.business, appt)
                if event_id:
                    appt.gcal_event_id = event_id
                    appt.calendar_synced = True
                    appt.save(update_fields=["gcal_event_id", "calendar_synced"])
                    synced += 1
            except Exception as e:
                self.message_user(request, f"Sync failed for {appt}: {e}", level="error")
        self.message_user(request, f"{synced} appointment(s) synced to Google Calendar.")


# ---------------------------------------------------------------------------
# SpamLog Admin
# ---------------------------------------------------------------------------

@admin.register(SpamLog)
class SpamLogAdmin(admin.ModelAdmin):
    list_display  = ("caller_phone", "business", "detection_reason", "action_badge", "is_whitelisted", "is_blacklisted", "detected_at")
    list_filter   = ("action_taken", "is_whitelisted", "is_blacklisted", "business")
    search_fields = ("caller_phone", "detection_reason")
    readonly_fields = ("id", "detected_at")
    date_hierarchy = "detected_at"
    actions = ["whitelist_numbers", "blacklist_numbers"]

    def action_badge(self, obj):
        colors = {"disconnected": "#F44336", "flagged": "#FF9800", "allowed": "#4CAF50"}
        color = colors.get(obj.action_taken, "#9E9E9E")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;">{}</span>',
            color, obj.get_action_taken_display()
        )
    action_badge.short_description = "Action Taken"

    @admin.action(description="Whitelist selected phone numbers")
    def whitelist_numbers(self, request, queryset):
        queryset.update(is_whitelisted=True, is_blacklisted=False)
        self.message_user(request, f"{queryset.count()} number(s) whitelisted.")

    @admin.action(description="Blacklist selected phone numbers")
    def blacklist_numbers(self, request, queryset):
        queryset.update(is_blacklisted=True, is_whitelisted=False)
        self.message_user(request, f"{queryset.count()} number(s) blacklisted.")


@admin.register(SpamBlocklist)
class SpamBlocklistAdmin(admin.ModelAdmin):
    list_display  = ("phone_number", "source", "added_at")
    search_fields = ("phone_number",)
    list_filter   = ("source",)


# ---------------------------------------------------------------------------
# UserProfile Admin
# ---------------------------------------------------------------------------

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ("user", "role", "business", "firebase_uid", "created_at")
    list_filter   = ("role",)
    search_fields = ("user__username", "firebase_uid", "user__email")
    readonly_fields = ("firebase_uid", "created_at")


# ---------------------------------------------------------------------------
# NotificationTemplate Admin
# ---------------------------------------------------------------------------

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display  = ("business", "trigger_type", "is_active")
    list_filter   = ("trigger_type", "is_active", "business")
    search_fields = ("business__business_name",)
