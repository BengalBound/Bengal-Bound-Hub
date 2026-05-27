from django.db import models
from accounts.models import User


class BudgetPeriod(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='budget_periods')
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class Budget(models.Model):
    STATUS = [('draft', 'Draft'), ('approved', 'Approved'), ('active', 'Active'), ('closed', 'Closed')]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='budgets')
    period = models.ForeignKey(BudgetPeriod, on_delete=models.CASCADE, related_name='budgets')
    name = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    total_budgeted = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_actual = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=5, default='USD')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_budgets')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_budgets')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.period})"

    @property
    def variance(self):
        return self.total_budgeted - self.total_actual

    @property
    def utilization_pct(self):
        if not self.total_budgeted:
            return 0
        return round(float(self.total_actual) / float(self.total_budgeted) * 100, 1)


class BudgetLine(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='lines')
    account_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True)
    budgeted_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['category', 'account_name']

    def __str__(self):
        return f"{self.account_name}: {self.budgeted_amount}"

    @property
    def variance(self):
        return self.budgeted_amount - self.actual_amount
