from django.contrib import admin
from .models import Website, SEOIssue

@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    pass

@admin.register(SEOIssue)
class SEOIssueAdmin(admin.ModelAdmin):
    pass

