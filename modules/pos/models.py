from django.db import models
from django.utils import timezone
from accounts.models import User


class POSConfig(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='pos_configs')
    name = models.CharField(max_length=100, default='Main Register')
    receipt_header = models.TextField(blank=True)
    receipt_footer = models.TextField(blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    currency = models.CharField(max_length=5, default='USD')
    allow_discount = models.BooleanField(default=True)
    allow_refund = models.BooleanField(default=True)
    cash_rounding = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.business.name})"


class POSSession(models.Model):
    STATUS = [('open', 'Open'), ('closed', 'Closed')]

    config = models.ForeignKey(POSConfig, on_delete=models.CASCADE, related_name='sessions')
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pos_sessions')
    status = models.CharField(max_length=10, choices=STATUS, default='open')
    opening_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_cash = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_sales = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_cash = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_card = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-opened_at']

    def __str__(self):
        return f"Session #{self.pk} — {self.config.name} ({self.get_status_display()})"

    def transaction_count(self):
        return self.orders.count()


class POSOrder(models.Model):
    STATUS = [('open', 'Open'), ('paid', 'Paid'), ('refunded', 'Refunded'), ('cancelled', 'Cancelled')]
    PAYMENT = [('cash', 'Cash'), ('card', 'Card'), ('mixed', 'Mixed'), ('pending', 'Pending')]

    session = models.ForeignKey(POSSession, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS, default='open')
    payment_method = models.CharField(max_length=20, choices=PAYMENT, default='pending')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_tendered = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    customer_name = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"POS-{self.order_number}"

    def recalculate(self):
        self.subtotal = self.items.aggregate(s=models.Sum('line_total'))['s'] or 0
        tax_rate = self.session.config.tax_rate
        self.tax_amount = round(self.subtotal * tax_rate / 100, 2)
        self.total = self.subtotal + self.tax_amount - self.discount_amount
        self.save(update_fields=['subtotal', 'tax_amount', 'total'])


class POSOrderItem(models.Model):
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('inventory.Product', on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['pk']

    def save(self, *args, **kwargs):
        discount = self.unit_price * self.quantity * self.discount_pct / 100
        self.line_total = (self.unit_price * self.quantity) - discount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
