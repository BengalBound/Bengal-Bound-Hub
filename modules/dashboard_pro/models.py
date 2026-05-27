from django.db import models
from accounts.models import User


class CustomDashboard(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='custom_dashboards')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-grid')
    color = models.CharField(max_length=7, default='#3b82f6')
    is_default = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)
    layout = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_dashboards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class DashboardWidget(models.Model):
    TYPE = [
        ('stat_card', 'Stat Card'), ('bar_chart', 'Bar Chart'), ('line_chart', 'Line Chart'),
        ('pie_chart', 'Pie/Donut Chart'), ('table', 'Data Table'), ('list', 'List'),
        ('calendar', 'Calendar'), ('map', 'Map'), ('gauge', 'Gauge'), ('text', 'Text/HTML'),
        ('recent_activity', 'Recent Activity'), ('quick_links', 'Quick Links'),
    ]

    dashboard = models.ForeignKey(CustomDashboard, on_delete=models.CASCADE, related_name='widgets')
    widget_type = models.CharField(max_length=30, choices=TYPE, default='stat_card')
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True)
    config = models.JSONField(default=dict, blank=True, help_text='Data source, filters, display options')
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    width = models.IntegerField(default=4, help_text='Grid columns (1-12)')
    height = models.IntegerField(default=2, help_text='Grid rows')
    refresh_interval = models.IntegerField(default=0, help_text='Seconds, 0=no auto-refresh')
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position_y', 'position_x']

    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()}) — {self.dashboard.name}"


class DashboardSharedUser(models.Model):
    ACCESS = [('view', 'View'), ('edit', 'Edit')]
    dashboard = models.ForeignKey(CustomDashboard, on_delete=models.CASCADE, related_name='shared_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_dashboards')
    access_level = models.CharField(max_length=10, choices=ACCESS, default='view')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('dashboard', 'user')]

    def __str__(self):
        return f"{self.user} → {self.dashboard} ({self.access_level})"
