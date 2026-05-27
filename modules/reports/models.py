from django.db import models
from accounts.models import User


class ReportDefinition(models.Model):
    TYPE = [('tabular', 'Tabular'), ('chart', 'Chart'), ('pivot', 'Pivot'), ('kpi', 'KPI Dashboard'), ('custom', 'Custom')]
    SOURCE = [('crm', 'CRM'), ('hr', 'HR'), ('accounting', 'Accounting'), ('inventory', 'Inventory'), ('sales', 'Sales'), ('custom', 'Custom Query')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='report_definitions')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=TYPE, default='tabular')
    data_source = models.CharField(max_length=20, choices=SOURCE, default='custom')
    query_config = models.JSONField(default=dict, blank=True, help_text='Filters, groupings, date ranges')
    chart_config = models.JSONField(default=dict, blank=True, help_text='Chart type, axes, colors')
    is_scheduled = models.BooleanField(default=False)
    schedule_cron = models.CharField(max_length=50, blank=True)
    recipients = models.TextField(blank=True, help_text='Comma-separated emails')
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ReportRun(models.Model):
    STATUS = [('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')]
    report = models.ForeignKey(ReportDefinition, on_delete=models.CASCADE, related_name='runs')
    status = models.CharField(max_length=20, choices=STATUS, default='running')
    parameters = models.JSONField(default=dict, blank=True)
    result_data = models.JSONField(default=dict, blank=True)
    row_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    run_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='report_runs')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.report.name} — {self.started_at}"


class Dashboard(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='report_dashboards')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    layout = models.JSONField(default=list, blank=True, help_text='Grid layout configuration')
    reports = models.ManyToManyField(ReportDefinition, blank=True, related_name='dashboards')
    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_dashboards')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
