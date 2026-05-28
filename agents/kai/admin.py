from django.contrib import admin
from .models import Pipeline, Incident

@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    pass

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    pass

