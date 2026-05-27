from django.db import models
from django.utils import timezone
from accounts.models import User


class ProductCategory(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='inv_categories')
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='inventory/categories/', null=True, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Product Categories'

    def __str__(self):
        return self.name


class UnitOfMeasure(models.Model):
    CATEGORY_CHOICES = [
        ('length', 'Length'),
        ('weight', 'Weight'),
        ('volume', 'Volume'),
        ('area', 'Area'),
        ('unit', 'Unit'),
        ('time', 'Time'),
        ('custom', 'Custom')
    ]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='inv_uoms')
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='unit')
    is_reference = models.BooleanField(default=False, help_text="Is this the reference unit for this category?")

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class UoMConversion(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='inv_uom_conversions')
    from_uom = models.ForeignKey(UnitOfMeasure, on_delete=models.CASCADE, related_name='conversions_from')
    to_uom = models.ForeignKey(UnitOfMeasure, on_delete=models.CASCADE, related_name='conversions_to')
    ratio = models.DecimalField(max_digits=12, decimal_places=6, help_text="Multiplier to convert from_uom to to_uom")

    class Meta:
        unique_together = [('from_uom', 'to_uom')]

    def __str__(self):
        return f"{self.from_uom} -> {self.to_uom} ({self.ratio})"


class Warehouse(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='inv_warehouses')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_warehouses')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    TYPE = [('storable', 'Storable'), ('consumable', 'Consumable'), ('service', 'Service')]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='inv_products')
    sku = models.CharField(max_length=100, blank=True)
    barcode = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=200)
    product_type = models.CharField(max_length=20, choices=TYPE, default='storable')
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='inventory/products/', null=True, blank=True)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=5, default='USD')
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    is_sold = models.BooleanField(default=True)
    is_purchased = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def stock_qty(self, warehouse=None):
        qs = self.stock_levels.filter(warehouse__business=self.business)
        if warehouse:
            qs = qs.filter(warehouse=warehouse)
        return qs.aggregate(s=models.Sum('quantity'))['s'] or 0


class ProductLot(models.Model):
    QMS_STATUS = [('pending', 'Pending QMS'), ('passed', 'Passed QMS'), ('failed', 'Failed QMS'), ('bypass', 'Bypass QMS')]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='lots')
    lot_number = models.CharField(max_length=100)
    manufacturing_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    qms_status = models.CharField(max_length=20, choices=QMS_STATUS, default='pending', help_text="Current quality control status of this batch")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('product', 'lot_number')]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} (Lot: {self.lot_number})"


class StockLevel(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_levels')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_levels')
    lot = models.ForeignKey(ProductLot, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_levels')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reserved_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('product', 'warehouse', 'lot')]

    def __str__(self):
        lot_str = f" [Lot: {self.lot.lot_number}]" if self.lot else ""
        return f"{self.product}{lot_str} @ {self.warehouse}: {self.quantity}"

    @property
    def available_qty(self):
        return self.quantity - self.reserved_qty


class StockMovement(models.Model):
    TYPE = [('in', 'Stock In'), ('out', 'Stock Out'), ('transfer', 'Transfer'), ('adjustment', 'Adjustment')]
    STATUS = [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done'), ('cancelled', 'Cancelled')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='inv_movements')
    reference = models.CharField(max_length=50, blank=True)
    movement_type = models.CharField(max_length=20, choices=TYPE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    lot = models.ForeignKey(ProductLot, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements')
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_movements')
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_movements')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stock_movements')
    movement_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-movement_date', '-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()}: {self.product} x{self.quantity}"

    def confirm(self):
        if self.status != 'draft':
            return
        if self.movement_type == 'in' and self.to_warehouse:
            level, _ = StockLevel.objects.get_or_create(product=self.product, warehouse=self.to_warehouse, lot=self.lot)
            level.quantity += self.quantity
            level.save()
        elif self.movement_type == 'out' and self.from_warehouse:
            level, _ = StockLevel.objects.get_or_create(product=self.product, warehouse=self.from_warehouse, lot=self.lot)
            level.quantity -= self.quantity
            level.save()
        elif self.movement_type == 'transfer':
            if self.from_warehouse:
                fl, _ = StockLevel.objects.get_or_create(product=self.product, warehouse=self.from_warehouse, lot=self.lot)
                fl.quantity -= self.quantity
                fl.save()
            if self.to_warehouse:
                tl, _ = StockLevel.objects.get_or_create(product=self.product, warehouse=self.to_warehouse, lot=self.lot)
                tl.quantity += self.quantity
                tl.save()
        self.status = 'done'
        self.save(update_fields=['status'])


class LabelTemplate(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='inv_label_templates')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    layout_data = models.TextField(help_text="Template structure (e.g. ZPL code or HTML layout for printing)")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PackagingLabel(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='inv_labels')
    template = models.ForeignKey(LabelTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    lot = models.ForeignKey(ProductLot, on_delete=models.CASCADE, related_name='labels')
    barcode_data = models.CharField(max_length=150, help_text="The scannable string generated for this specific label")
    printed_at = models.DateTimeField(null=True, blank=True)
    printed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-printed_at']

    def __str__(self):
        return f"Label for {self.lot.lot_number}"
