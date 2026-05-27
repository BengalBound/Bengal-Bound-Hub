from django.db import models
from accounts.models import User


class HubPresentation(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='presentations')
    title = models.CharField(max_length=300, default='Untitled Presentation')
    theme = models.CharField(max_length=30, default='dark')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_presentations')
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

    @property
    def slide_count(self):
        return self.slides.count()


class HubSlide(models.Model):
    LAYOUTS = [
        ('title', 'Title Slide'),
        ('content', 'Title + Content'),
        ('two_col', 'Two Columns'),
        ('blank', 'Blank'),
        ('image', 'Image Focus'),
    ]

    presentation = models.ForeignKey(HubPresentation, on_delete=models.CASCADE, related_name='slides')
    position = models.PositiveIntegerField(default=0)
    layout = models.CharField(max_length=20, choices=LAYOUTS, default='content')
    title = models.CharField(max_length=300, blank=True)
    body = models.TextField(blank=True, help_text="Main slide content / bullet points")
    notes = models.TextField(blank=True, help_text="Speaker notes")
    background_color = models.CharField(max_length=30, blank=True)
    image = models.ImageField(upload_to='slides/images/', null=True, blank=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"Slide {self.position + 1}: {self.title or '(no title)'}"
