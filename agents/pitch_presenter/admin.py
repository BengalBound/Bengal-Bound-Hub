from django.contrib import admin
from agents.pitch_presenter.models import VideoPitch, PresentationSlide


class PresentationSlideInline(admin.TabularInline):
    model = PresentationSlide
    extra = 0
    fields = ['slide_number', 'image_url', 'talking_points']


@admin.register(VideoPitch)
class VideoPitchAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['title', 'target_audience']
    inlines = [PresentationSlideInline]
