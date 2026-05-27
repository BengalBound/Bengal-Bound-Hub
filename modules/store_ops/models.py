from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class RetailStore(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='retail_stores')
    name = models.CharField(max_length=150)
    address = models.TextField(blank=True)
    manager = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_stores')
    phone = models.CharField(max_length=30, blank=True)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class StoreReport(models.Model):
    store = models.ForeignKey(RetailStore, on_delete=models.CASCADE, related_name='reports')
    report_date = models.DateField()
    sales_total = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    transaction_count = models.IntegerField(null=True, blank=True)
    top_selling_product = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    submitted_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_store_reports')
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-report_date']
        unique_together = ['store', 'report_date']

    def __str__(self):
        return f"{self.store.name} — {self.report_date}"


class StoreTask(models.Model):
    PRIORITY = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    store = models.ForeignKey(RetailStore, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='store_tasks')
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=8, choices=PRIORITY, default='medium')
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_done', '-priority', 'due_date']

    def __str__(self):
        return f"{self.store.name}: {self.title}"
