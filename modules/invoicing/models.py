from django.db import models
from django.utils import timezone
from accounts.models import User


class InvoiceClient(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='inv_clients')
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    company = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    currency = models.CharField(max_length=5, default='USD')
    payment_terms = models.IntegerField(default=30, help_text='Days')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.company or self.name


class Invoice(models.Model):
    STATUS = [('draft', 'Draft'), ('sent', 'Sent'), ('viewed', 'Viewed'), ('partial', 'Partially Paid'), ('paid', 'Paid'), ('overdue', 'Overdue'), ('cancelled', 'Cancelled')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='inv_invoices')
    invoice_number = models.CharField(max_length=50)
    client = models.ForeignKey(InvoiceClient, on_delete=models.PROTECT, related_name='invoices')
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=5, default='USD')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date', '-created_at']

    def __str__(self):
        return f"INV-{self.invoice_number} | {self.client}"

    @property
    def balance_due(self):
        return self.total - self.amount_paid

    @property
    def is_overdue(self):
        return self.due_date and self.due_date < timezone.now().date() and self.status not in ('paid', 'cancelled')

    def recalculate(self):
        self.subtotal = self.lines.aggregate(s=models.Sum('line_total'))['s'] or 0
        self.total = self.subtotal + self.tax_amount - self.discount_amount
        self.save(update_fields=['subtotal', 'total'])


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ['pk']

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description}: {self.line_total}"


class Payment(models.Model):
    METHOD = [('cash', 'Cash'), ('bank_transfer', 'Bank Transfer'), ('card', 'Card'), ('cheque', 'Cheque'), ('online', 'Online'), ('other', 'Other')]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    method = models.CharField(max_length=20, choices=METHOD, default='bank_transfer')
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_payments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment: {self.amount} for {self.invoice}"
