from django.contrib import admin
from .models import ResearchConfig, ResearchReport

@admin.register(ResearchConfig)
class ResearchConfigAdmin(admin.ModelAdmin):
    pass

@admin.register(ResearchReport)
class ResearchReportAdmin(admin.ModelAdmin):
    pass

