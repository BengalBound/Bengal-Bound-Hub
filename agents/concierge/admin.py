from django.contrib import admin
from .models import MeetingRequest, EmailTriage

@admin.register(MeetingRequest)
class MeetingRequestAdmin(admin.ModelAdmin):
    pass

@admin.register(EmailTriage)
class EmailTriageAdmin(admin.ModelAdmin):
    pass

