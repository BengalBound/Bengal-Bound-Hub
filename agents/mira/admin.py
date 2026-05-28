from django.contrib import admin
from .models import ClientHealth, SuccessEmail

@admin.register(ClientHealth)
class ClientHealthAdmin(admin.ModelAdmin):
    pass

@admin.register(SuccessEmail)
class SuccessEmailAdmin(admin.ModelAdmin):
    pass

