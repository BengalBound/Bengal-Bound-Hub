from django.db import models


class DataSet(models.Model):
    SOURCE = [
        ('manual', 'Manual Entry'),
        ('csv', 'CSV Import'),
        ('json', 'JSON Import'),
    ]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='datasets')
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=300, blank=True)
    source = models.CharField(max_length=10, choices=SOURCE, default='manual')
    columns = models.JSONField(default=list)  # ['Name', 'Value', 'Date', ...]
    rows = models.JSONField(default=list)     # [['Alice', 100, '2024-01'], ...]
    tags = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = [('business', 'name')]

    def __str__(self):
        return self.name

    @property
    def row_count(self):
        return len(self.rows)

    @property
    def col_count(self):
        return len(self.columns)


class AnalyticsChart(models.Model):
    CHART_TYPES = [
        ('table', 'Data Table'),
        ('bar', 'Bar Chart'),
        ('line', 'Line Chart'),
        ('pie', 'Pie / Donut Chart'),
        ('scatter', 'Scatter Plot'),
        ('area', 'Area Chart'),
        ('pivot', 'Pivot Summary'),
    ]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='analytics_charts')
    dataset = models.ForeignKey(DataSet, on_delete=models.CASCADE, related_name='charts')
    name = models.CharField(max_length=150)
    chart_type = models.CharField(max_length=10, choices=CHART_TYPES, default='table')
    x_column = models.CharField(max_length=100, blank=True)
    y_column = models.CharField(max_length=100, blank=True)
    group_column = models.CharField(max_length=100, blank=True)
    filter_config = models.JSONField(default=dict, blank=True)
    config = models.JSONField(default=dict, blank=True)  # additional chart config
    is_pinned = models.BooleanField(default=False)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_chart_type_display()})"


class DataStudioReport(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='studio_reports')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    charts = models.ManyToManyField(AnalyticsChart, blank=True, related_name='reports')
    is_shared = models.BooleanField(default=False)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name
