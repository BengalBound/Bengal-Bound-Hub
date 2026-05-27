from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'service_type', 'date', 'time', 'status')
    list_filter = ('service_type', 'status', 'date')
    search_fields = ('client_name', 'client_email', 'client_phone')
