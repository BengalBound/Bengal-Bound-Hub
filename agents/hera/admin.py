from django.contrib import admin
from .models import PolicyQuery, OnboardingTask

@admin.register(PolicyQuery)
class PolicyQueryAdmin(admin.ModelAdmin):
    pass

@admin.register(OnboardingTask)
class OnboardingTaskAdmin(admin.ModelAdmin):
    pass

