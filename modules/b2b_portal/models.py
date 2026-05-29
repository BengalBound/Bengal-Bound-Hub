from django.db import models
from hub.models import BusinessInstance


class B2BCustomer(models.Model):
    PRICE_TIERS = [
        ('standard', 'Standard'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='b2b_customers')
    company_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    price_tier = models.CharField(max_length=10, choices=PRICE_TIERS, default='standard')
    credit_limit = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    outstanding_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name

    @property
    def available_credit(self):
        if self.credit_limit is None:
            return None
        return self.credit_limit - self.outstanding_balance


class B2BOrder(models.Model):
    STATUS = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='b2b_orders')
    customer = models.ForeignKey(B2BCustomer, on_delete=models.CASCADE, related_name='orders')
    reference_no = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=12, choices=STATUS, default='draft')
    notes = models.TextField(blank=True)
    ordered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-ordered_at']

    def __str__(self):
        return f"Order #{self.pk} — {self.customer.company_name}"

    @property
    def total_amount(self):
        return sum(line.line_total for line in self.lines.all())

    @property
    def line_count(self):
        return self.lines.count()


class B2BOrderLine(models.Model):
    order = models.ForeignKey(B2BOrder, on_delete=models.CASCADE, related_name='lines')
    product_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, blank=True)
    qty = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=30, blank=True)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['pk']

    @property
    def line_total(self):
        return self.qty * self.unit_price
