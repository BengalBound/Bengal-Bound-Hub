from django.contrib import admin
from .models import TrafficLog, Coupon, WaaSSite, AIEmployeeTier, HiredAIEmployee, UserNotification, Order, Affiliate

@admin.register(TrafficLog)
class TrafficLogAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'is_consent_given', 'timestamp')
    list_filter = ('is_consent_given', 'timestamp')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percentage', 'is_active', 'valid_from', 'valid_until')
    list_filter = ('is_active',)

@admin.register(WaaSSite)
class WaaSSiteAdmin(admin.ModelAdmin):
    list_display = ('domain', 'client', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('domain', 'client__email')

@admin.register(AIEmployeeTier)
class AIEmployeeTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'token_limit')

@admin.register(HiredAIEmployee)
class HiredAIEmployeeAdmin(admin.ModelAdmin):
    list_display = ('ai_name', 'employer', 'tier', 'is_active', 'tokens_used_this_month', 'hired_at')
    list_filter = ('is_active', 'tier')
    search_fields = ('ai_name', 'employer__email')

@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('title', 'message', 'user__email')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('client__email', 'description')

@admin.register(Affiliate)
class AffiliateAdmin(admin.ModelAdmin):
    list_display = ('user', 'affiliate_code', 'commission_balance', 'total_earned', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('user__email', 'affiliate_code')

from .models import Project, Task, FinanceRecord

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'manager', 'status', 'deadline')
    list_filter = ('status',)
    search_fields = ('title', 'client__email', 'manager__email')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'assigned_to', 'priority', 'status', 'due_date')
    list_filter = ('status', 'priority')
    search_fields = ('title', 'project__title', 'assigned_to__email')

@admin.register(FinanceRecord)
class FinanceRecordAdmin(admin.ModelAdmin):
    list_display = ('title', 'record_type', 'amount', 'date', 'category')
    list_filter = ('record_type', 'category', 'date')
    search_fields = ('title', 'category')
