from django.contrib import admin
from .models import Event, Attendee

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    pass

@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
    pass

