from django.db import models
from django.utils import timezone
from accounts.models import User


class OperationalReport(models.Model):
    TYPES = [
        ('daily_ops', 'Daily Operations'),
        ('sales_summary', 'Sales Summary'),
        ('expense_report', 'Expense Report'),
        ('incident', 'Incident Report'),
        ('performance', 'Performance Report'),
        ('custom', 'Custom Report'),
    ]
    STATUS = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='op_reports')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_op_reports')
    report_type = models.CharField(max_length=20, choices=TYPES, default='daily_ops')
    title = models.CharField(max_length=200)
    period_start = models.DateField(default=timezone.now)
    period_end = models.DateField(default=timezone.now)
    content = models.TextField(help_text="Full report body")
    summary = models.TextField(blank=True, help_text="Short executive summary")
    status = models.CharField(max_length=20, choices=STATUS, default='draft')

    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_op_reports'
    )
    review_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.get_status_display()}"


class UserExpense(models.Model):
    STATUS = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='user_expenses')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_expenses')
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category_name = models.CharField(max_length=100, help_text="e.g. Travel, Meals, Supplies")
    department = models.CharField(max_length=100, blank=True)
    expense_date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)
    receipt = models.FileField(upload_to='financials/receipts/', null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_user_expenses'
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        return f"{self.title} — {self.amount} ({self.get_status_display()})"
