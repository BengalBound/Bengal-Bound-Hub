from django.contrib import admin
from .models import BrandMention, PressRelease

@admin.register(BrandMention)
class BrandMentionAdmin(admin.ModelAdmin):
    pass

@admin.register(PressRelease)
class PressReleaseAdmin(admin.ModelAdmin):
    pass

