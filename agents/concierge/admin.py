from django.contrib import admin
from .models import MeetingRequest, EmailTriage

admin.site.register(MeetingRequest)
admin.site.register(EmailTriage)
