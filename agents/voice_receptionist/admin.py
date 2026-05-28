from django.contrib import admin
from .models import BusinessProfile, Call, Appointment, SpamLog, SpamBlocklist, UserProfile, NotificationTemplate

@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    pass

@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    pass

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    pass

@admin.register(SpamLog)
class SpamLogAdmin(admin.ModelAdmin):
    pass

@admin.register(SpamBlocklist)
class SpamBlocklistAdmin(admin.ModelAdmin):
    pass

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    pass

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    pass

