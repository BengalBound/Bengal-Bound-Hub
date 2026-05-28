from django.contrib import admin
from .models import ContentCalendar, CalendarEntry

@admin.register(ContentCalendar)
class ContentCalendarAdmin(admin.ModelAdmin):
    pass

@admin.register(CalendarEntry)
class CalendarEntryAdmin(admin.ModelAdmin):
    pass

