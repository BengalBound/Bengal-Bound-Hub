from django.db import models
from hub.models import BusinessInstance


class Employee(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="employee_set")
    employee_id = models.CharField(max_length=50)
    name = models.CharField(max_length=300)
    email = models.EmailField()
    department = models.CharField(max_length=200)
    join_date = models.DateField()
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    house_rent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medical = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bank_account = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=200)
    tin_number = models.CharField(max_length=50, blank=True)
    pf_enrolled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.employee_id})"


class PayrollRun(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="payrollrun_set")
    month = models.DateField()
    total_gross = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_net = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    employee_count = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[("draft", "Draft"), ("approved", "Approved"), ("transferred", "Transferred")],
        default="draft",
    )
    ai_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-month"]

    def __str__(self):
        return f"Payroll {self.month} [{self.status}]"
