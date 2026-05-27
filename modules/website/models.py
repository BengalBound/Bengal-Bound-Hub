from django.db import models
from accounts.models import User


class WebsiteProject(models.Model):
    STATUS = [('draft', 'Draft'), ('in_progress', 'In Progress'), ('review', 'In Review'), ('live', 'Live'), ('paused', 'Paused')]
    TYPE = [('landing', 'Landing Page'), ('business', 'Business Site'), ('ecommerce', 'eCommerce'), ('blog', 'Blog'), ('portfolio', 'Portfolio'), ('other', 'Other')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='website_projects')
    name = models.CharField(max_length=200)
    website_type = models.CharField(max_length=20, choices=TYPE, default='business')
    domain = models.CharField(max_length=200, blank=True)
    staging_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    template_used = models.CharField(max_length=100, blank=True)
    color_scheme = models.JSONField(default=dict, blank=True)
    favicon = models.ImageField(upload_to='website/favicons/', null=True, blank=True)
    logo = models.ImageField(upload_to='website/logos/', null=True, blank=True)
    description = models.TextField(blank=True)
    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.TextField(blank=True, max_length=500)
    google_analytics_id = models.CharField(max_length=30, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_websites')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_websites')
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class WebPage(models.Model):
    STATUS = [('draft', 'Draft'), ('published', 'Published'), ('archived', 'Archived')]
    project = models.ForeignKey(WebsiteProject, on_delete=models.CASCADE, related_name='pages')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    content = models.TextField(blank=True)
    blocks = models.JSONField(default=list, blank=True, help_text='Page builder blocks')
    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.TextField(blank=True, max_length=500)
    is_homepage = models.BooleanField(default=False)
    in_navigation = models.BooleanField(default=True)
    nav_order = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_pages')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nav_order', 'title']
        unique_together = [('project', 'slug')]

    def __str__(self):
        return f"{self.title} ({self.project.name})"


class WebsiteAsset(models.Model):
    TYPE = [('image', 'Image'), ('video', 'Video'), ('document', 'Document'), ('font', 'Font'), ('other', 'Other')]
    project = models.ForeignKey(WebsiteProject, on_delete=models.CASCADE, related_name='assets')
    name = models.CharField(max_length=200)
    asset_type = models.CharField(max_length=20, choices=TYPE, default='image')
    file = models.FileField(upload_to='website/assets/')
    alt_text = models.CharField(max_length=300, blank=True)
    file_size = models.BigIntegerField(default=0)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='website_assets')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
