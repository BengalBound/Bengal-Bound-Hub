from django.db import models
from accounts.models import User


class SalaryStructure(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='payroll_structures')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SalaryComponent(models.Model):
    TYPE = [('earning', 'Earning'), ('deduction', 'Deduction')]
    CALC = [('fixed', 'Fixed Amount'), ('percentage', 'Percentage of Basic'), ('formula', 'Formula')]

    structure = models.ForeignKey(SalaryStructure, on_delete=models.CASCADE, related_name='components')
    name = models.CharField(max_length=100)
    component_type = models.CharField(max_length=15, choices=TYPE)
    calculation_type = models.CharField(max_length=15, choices=CALC, default='fixed')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_taxable = models.BooleanField(default=True)
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ['component_type', 'position']

    def __str__(self):
        return f"{self.name} ({self.get_component_type_display()})"


class PayPeriod(models.Model):
    FREQ = [('weekly', 'Weekly'), ('biweekly', 'Bi-Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly')]
    STATUS = [('draft', 'Draft'), ('processing', 'Processing'), ('paid', 'Paid'), ('cancelled', 'Cancelled')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='payroll_periods')
    name = models.CharField(max_length=100)
    frequency = models.CharField(max_length=20, choices=FREQ, default='monthly')
    start_date = models.DateField()
    end_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payrolls')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"

    def total_gross(self):
        return self.payslips.aggregate(s=models.Sum('gross_pay'))['s'] or 0

    def total_net(self):
        return self.payslips.aggregate(s=models.Sum('net_pay'))['s'] or 0


class Payslip(models.Model):
    STATUS = [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('paid', 'Paid')]

    pay_period = models.ForeignKey(PayPeriod, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey('hr.Employee', on_delete=models.CASCADE, related_name='payslips')
    structure = models.ForeignKey(SalaryStructure, on_delete=models.SET_NULL, null=True, blank=True)
    basic_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=5, default='USD')
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [('pay_period', 'employee')]

    def __str__(self):
        return f"Payslip: {self.employee} ({self.pay_period})"


class PayslipLine(models.Model):
    TYPE = [('earning', 'Earning'), ('deduction', 'Deduction')]
    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='lines')
    component = models.ForeignKey(SalaryComponent, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    line_type = models.CharField(max_length=15, choices=TYPE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.name}: {self.amount}"
