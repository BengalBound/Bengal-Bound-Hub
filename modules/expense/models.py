from django.db import models
from django.utils import timezone
from accounts.models import User


class ExpenseCategory(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='expense_categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    budget_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    color = models.CharField(max_length=7, default='#3b82f6')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ExpenseClaim(models.Model):
    STATUS = [('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('paid', 'Paid')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='expense_claims')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expense_claims')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=5, default='USD')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_expense_claims')
    review_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    payment_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.submitted_by}"

    def recalculate_total(self):
        self.total_amount = self.items.aggregate(s=models.Sum('amount'))['s'] or 0
        self.save(update_fields=['total_amount'])


class ExpenseItem(models.Model):
    claim = models.ForeignKey(ExpenseClaim, on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=300)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField(default=timezone.now)
    receipt = models.FileField(upload_to='expense/receipts/', null=True, blank=True)
    vendor = models.CharField(max_length=100, blank=True)
    is_billable = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['expense_date']

    def __str__(self):
        return f"{self.description}: {self.amount}"
