from django.contrib import admin
from .models import ReportConfig, Report

@admin.register(ReportConfig)
class ReportConfigAdmin(admin.ModelAdmin):
    pass

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    pass

