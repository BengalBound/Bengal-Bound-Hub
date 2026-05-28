from django.contrib import admin
from .models import ExecTask, MeetingBrief

@admin.register(ExecTask)
class ExecTaskAdmin(admin.ModelAdmin):
    pass

@admin.register(MeetingBrief)
class MeetingBriefAdmin(admin.ModelAdmin):
    pass

