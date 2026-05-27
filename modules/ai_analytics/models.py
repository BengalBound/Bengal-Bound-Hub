from django.db import models
from accounts.models import User


class AnalyticsDataset(models.Model):
    SOURCE = [('manual', 'Manual Upload'), ('crm', 'CRM'), ('hr', 'HR'), ('accounting', 'Accounting'), ('inventory', 'Inventory'), ('pos', 'POS'), ('ecommerce', 'eCommerce'), ('external', 'External API')]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='analytics_datasets')
    name = models.CharField(max_length=200)
    source = models.CharField(max_length=20, choices=SOURCE, default='manual')
    description = models.TextField(blank=True)
    schema = models.JSONField(default=dict, blank=True)
    row_count = models.IntegerField(default=0)
    last_refreshed = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AIInsight(models.Model):
    TYPE = [('trend', 'Trend Analysis'), ('anomaly', 'Anomaly Detection'), ('forecast', 'Forecast'), ('recommendation', 'Recommendation'), ('summary', 'Summary')]
    STATUS = [('pending', 'Pending'), ('generated', 'Generated'), ('failed', 'Failed'), ('dismissed', 'Dismissed')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='ai_insights')
    dataset = models.ForeignKey(AnalyticsDataset, on_delete=models.SET_NULL, null=True, blank=True)
    insight_type = models.CharField(max_length=20, choices=TYPE)
    title = models.CharField(max_length=300)
    summary = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    chart_data = models.JSONField(default=dict, blank=True)
    confidence_score = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    generated_by = models.CharField(max_length=100, blank=True, help_text='AI model used')
    is_actionable = models.BooleanField(default=False)
    action_taken = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class KPIMetric(models.Model):
    PERIOD = [('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual')]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='kpi_metrics')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    value = models.DecimalField(max_digits=16, decimal_places=4, default=0)
    target = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    period = models.CharField(max_length=20, choices=PERIOD, default='monthly')
    period_date = models.DateField()
    source_module = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_date', 'name']

    def __str__(self):
        return f"{self.name}: {self.value} ({self.period_date})"

    @property
    def achievement_pct(self):
        if not self.target or self.target == 0:
            return None
        return round(float(self.value) / float(self.target) * 100, 1)
