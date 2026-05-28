from django.contrib import admin
from .models import TranslationJob, TranslationOutput

@admin.register(TranslationJob)
class TranslationJobAdmin(admin.ModelAdmin):
    pass

@admin.register(TranslationOutput)
class TranslationOutputAdmin(admin.ModelAdmin):
    pass

