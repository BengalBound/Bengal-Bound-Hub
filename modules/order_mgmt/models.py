from django.db import models
from django.utils import timezone
from accounts.models import User


class Vendor(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='po_vendors')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    payment_terms = models.IntegerField(default=30, help_text='Net days')
    currency = models.CharField(max_length=5, default='USD')
    tax_id = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    STATUS = [('draft', 'Draft'), ('sent', 'Sent to Vendor'), ('confirmed', 'Confirmed'), ('partial', 'Partially Received'), ('received', 'Fully Received'), ('cancelled', 'Cancelled')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='purchase_orders')
    po_number = models.CharField(max_length=50)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    order_date = models.DateField(default=timezone.now)
    expected_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=5, default='USD')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_pos')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_pos')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-order_date', '-created_at']

    def __str__(self):
        return f"PO-{self.po_number} | {self.vendor}"

    def recalculate(self):
        self.subtotal = self.lines.aggregate(s=models.Sum('line_total'))['s'] or 0
        self.total = self.subtotal + self.tax_amount
        self.save(update_fields=['subtotal', 'total'])


class PurchaseOrderLine(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey('inventory.Product', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    received_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ['pk']

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description}: {self.quantity} x {self.unit_price}"
