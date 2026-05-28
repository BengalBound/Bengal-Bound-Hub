from django.contrib import admin
from .models import FeedbackSurvey, InsightTheme

@admin.register(FeedbackSurvey)
class FeedbackSurveyAdmin(admin.ModelAdmin):
    pass

@admin.register(InsightTheme)
class InsightThemeAdmin(admin.ModelAdmin):
    pass

