from django.contrib import admin
from .models import (
    BusinessInstance, ModuleCatalog, TenantModule,
    BusinessEmployee, ConnectorSession, SyncLog,
)


@admin.register(BusinessInstance)
class BusinessInstanceAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'business_type', 'installation_type', 'owner', 'is_active', 'created_at')
    list_filter = ('business_type', 'installation_type', 'is_active', 'is_verified')
    search_fields = ('name', 'slug', 'owner__email')
    readonly_fields = ('created_at', 'updated_at', 'last_synced_at', 'storage_used_mb')
    fieldsets = (
        ('Identity', {'fields': ('owner', 'name', 'slug', 'business_type', 'installation_type', 'tagline', 'logo')}),
        ('Contact', {'fields': ('business_email', 'business_phone', 'business_address')}),
        ('Storage', {'fields': ('storage_used_mb', 'storage_limit_mb')}),
        ('IP Lock', {'fields': ('allowed_ips',)}),
        ('Self-Hosted Sync', {'fields': ('sync_token', 'self_hosted_url', 'last_synced_at')}),
        ('Status', {'fields': ('is_active', 'is_verified', 'created_at', 'updated_at')}),
    )


@admin.register(ModuleCatalog)
class ModuleCatalogAdmin(admin.ModelAdmin):
    list_display = ('name', 'module_id', 'category', 'is_free', 'monthly_price_usd', 'is_available', 'is_coming_soon', 'display_order')
    list_filter = ('category', 'is_free', 'is_available', 'is_coming_soon')
    search_fields = ('name', 'module_id')
    ordering = ('display_order', 'name')


@admin.register(TenantModule)
class TenantModuleAdmin(admin.ModelAdmin):
    list_display = ('business', 'module', 'tier', 'is_active', 'activated_at', 'expires_at')
    list_filter = ('tier', 'is_active')
    search_fields = ('business__name', 'module__name')
    raw_id_fields = ('business', 'module')


@admin.register(BusinessEmployee)
class BusinessEmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'employee_id', 'business', 'role', 'email', 'is_active', 'joined_at')
    list_filter = ('role', 'is_active')
    search_fields = ('name', 'email', 'business__name', 'employee_id')
    raw_id_fields = ('business', 'user')


@admin.register(ConnectorSession)
class ConnectorSessionAdmin(admin.ModelAdmin):
    list_display = ('label', 'business', 'device_ip', 'is_active', 'created_at', 'expires_at')
    list_filter = ('is_active',)
    search_fields = ('label', 'business__name', 'token')
    readonly_fields = ('token', 'created_at', 'last_used_at')


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('business', 'sync_type', 'status', 'records_synced', 'started_at', 'completed_at')
    list_filter = ('sync_type', 'status')
    search_fields = ('business__name',)
    readonly_fields = ('started_at',)
