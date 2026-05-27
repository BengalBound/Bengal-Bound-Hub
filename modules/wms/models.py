from django.db import models
from django.utils import timezone


class WarehouseZone(models.Model):
    ZONE_TYPES = [
        ('receiving', 'Receiving'), ('storage', 'Storage'),
        ('picking', 'Picking Area'), ('packing', 'Packing / Dispatch'),
        ('shipping', 'Shipping Dock'), ('returns', 'Returns Processing'),
        ('hazmat', 'Hazmat / Controlled'), ('cold', 'Cold Storage'),
        ('overflow', 'Overflow'),
    ]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='warehouse_zones')
    name = models.CharField(max_length=80)
    zone_type = models.CharField(max_length=15, choices=ZONE_TYPES, default='storage')
    description = models.CharField(max_length=200, blank=True)
    capacity_bins = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('business', 'name')]
        ordering = ['zone_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_zone_type_display()})"

    @property
    def used_bins(self):
        return self.bins.filter(is_occupied=True).count()

    @property
    def available_bins(self):
        return self.bins.filter(is_occupied=False).count()


class StorageBin(models.Model):
    zone = models.ForeignKey(WarehouseZone, on_delete=models.CASCADE, related_name='bins')
    bin_code = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True)
    is_occupied = models.BooleanField(default=False)
    current_sku = models.CharField(max_length=80, blank=True)
    current_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = [('zone', 'bin_code')]
        ordering = ['bin_code']

    def __str__(self):
        return f"{self.zone.name} / {self.bin_code}"


class InboundReceipt(models.Model):
    STATUS = [
        ('expected', 'Expected'), ('partial', 'Partially Received'),
        ('complete', 'Complete'), ('over', 'Over-received'),
        ('cancelled', 'Cancelled'),
    ]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='inbound_receipts')
    receipt_number = models.CharField(max_length=20)
    supplier_name = models.CharField(max_length=150)
    purchase_order_ref = models.CharField(max_length=100, blank=True)
    carrier_name = models.CharField(max_length=100, blank=True)
    tracking_ref = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=15, choices=STATUS, default='expected')
    expected_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)
    received_by = models.ForeignKey('bredbound.BusinessEmployee', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('business', 'receipt_number')]
        ordering = ['-created_at']

    def __str__(self):
        return f"GRN-{self.receipt_number}: {self.supplier_name}"

    @property
    def total_expected(self):
        return sum(l.expected_qty for l in self.lines.all())

    @property
    def total_received(self):
        return sum(l.received_qty for l in self.lines.all())


class InboundReceiptLine(models.Model):
    receipt = models.ForeignKey(InboundReceipt, on_delete=models.CASCADE, related_name='lines')
    item_description = models.CharField(max_length=200)
    sku = models.CharField(max_length=80, blank=True)
    expected_qty = models.DecimalField(max_digits=10, decimal_places=2)
    received_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, blank=True)
    bin = models.ForeignKey(StorageBin, on_delete=models.SET_NULL, null=True, blank=True, related_name='receipt_lines')
    notes = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.receipt} — {self.item_description}"

    @property
    def variance(self):
        return self.received_qty - self.expected_qty


class PickList(models.Model):
    STATUS = [
        ('pending', 'Pending'), ('picking', 'Picking in Progress'),
        ('picked', 'Fully Picked'), ('packed', 'Packed'),
        ('dispatched', 'Dispatched'), ('cancelled', 'Cancelled'),
    ]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='pick_lists')
    pick_number = models.CharField(max_length=20)
    order_reference = models.CharField(max_length=100, blank=True)
    customer_name = models.CharField(max_length=150, blank=True)
    customer_address = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS, default='pending')
    assigned_to = models.ForeignKey('bredbound.BusinessEmployee', on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    courier_name = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('business', 'pick_number')]
        ordering = ['-created_at']

    def __str__(self):
        return f"PL-{self.pick_number}"

    @property
    def completion_pct(self):
        items = self.items.all()
        if not items:
            return 0
        picked = items.filter(is_picked=True).count()
        return int(picked / items.count() * 100)


class PickListItem(models.Model):
    pick_list = models.ForeignKey(PickList, on_delete=models.CASCADE, related_name='items')
    item_description = models.CharField(max_length=200)
    sku = models.CharField(max_length=80, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, blank=True)
    bin = models.ForeignKey(StorageBin, on_delete=models.SET_NULL, null=True, blank=True, related_name='pick_items')
    picked_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_picked = models.BooleanField(default=False)

    class Meta:
        ordering = ['bin__bin_code', 'item_description']

    def __str__(self):
        return f"{self.pick_list} — {self.item_description}"
