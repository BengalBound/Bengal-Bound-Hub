from django.contrib import admin
from .models import Prospect, OutreachSequence

@admin.register(Prospect)
class ProspectAdmin(admin.ModelAdmin):
    pass

@admin.register(OutreachSequence)
class OutreachSequenceAdmin(admin.ModelAdmin):
    pass

