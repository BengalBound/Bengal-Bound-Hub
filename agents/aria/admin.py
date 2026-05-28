from django.contrib import admin
from agents.aria.models import SupportTicket, TicketResponse

class TicketResponseInline(admin.StackedInline):
    model = TicketResponse
    extra = 0

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['subject', 'business', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority', 'channel']
    search_fields = ['subject', 'customer_email']
    inlines = [TicketResponseInline]
