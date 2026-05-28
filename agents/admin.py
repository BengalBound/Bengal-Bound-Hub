from django.contrib import admin
from .models import AgentInstance, AgentLog, AgentPermissionRequest, AgentIntegration, AgentWebhookEndpoint, AgentCatalog, AgentMemory

class AgentLogInline(admin.TabularInline):
    model = AgentLog
    extra = 0
    readonly_fields = ['action', 'outcome', 'detail', 'model_used', 'tokens']
    can_delete = False
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by('-created_at')[:20]

class AgentPermissionRequestInline(admin.StackedInline):
    model = AgentPermissionRequest
    extra = 0
    readonly_fields = ['context', 'option_a', 'option_b']

@admin.register(AgentInstance)
class AgentInstanceAdmin(admin.ModelAdmin):
    list_display = ['business', 'catalog', 'status', 'tokens_used_this_month']
    list_filter = ['status', 'catalog']
    search_fields = ['business__name']
    inlines = [AgentPermissionRequestInline, AgentLogInline]

@admin.register(AgentCatalog)
class AgentCatalogAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'is_active']
    
@admin.register(AgentMemory)
class AgentMemoryAdmin(admin.ModelAdmin):
    list_display = ['instance', 'subject', 'memory_type', 'importance']
    
@admin.register(AgentIntegration)
class AgentIntegrationAdmin(admin.ModelAdmin):
    list_display = ['instance', 'platform', 'label', 'status']

@admin.register(AgentWebhookEndpoint)
class AgentWebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ['instance', 'source', 'url_token', 'is_active']
