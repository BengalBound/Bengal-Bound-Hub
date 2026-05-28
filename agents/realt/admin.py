from django.contrib import admin
from .models import Property, Lead

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    pass

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    pass

