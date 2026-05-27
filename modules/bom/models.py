from django.db import models
from django.utils import timezone
from accounts.models import User


class BillOfMaterials(models.Model):
    TYPE = [('manufacture', 'Manufacture'), ('phantom', 'Phantom'), ('kit', 'Kit')]
    STATUS = [('draft', 'Draft'), ('active', 'Active'), ('obsolete', 'Obsolete')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='boms')
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='boms')
    bom_type = models.CharField(max_length=20, choices=TYPE, default='manufacture')
    version = models.CharField(max_length=20, default='1.0')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    uom = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    notes = models.TextField(blank=True)
    effective_date = models.DateField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_boms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bill of Materials'
        verbose_name_plural = 'Bills of Materials'

    def __str__(self):
        return f"BOM: {self.product.name} v{self.version}"


class BOMComponent(models.Model):
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name='components')
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='used_in_boms')
    quantity = models.DecimalField(max_digits=10, decimal_places=4)
    uom = models.CharField(max_length=20, blank=True)
    scrap_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Scrap/waste percentage')
    expected_yield_pct = models.DecimalField(max_digits=5, decimal_places=2, default=100, help_text='Expected material yield percentage')
    is_tooling = models.BooleanField(default=False, help_text='Is this a consumable tooling asset (e.g. Mold/Die)?')
    tooling_consumed_per_unit = models.DecimalField(max_digits=10, decimal_places=4, default=0, help_text='Tooling lifespan shots/uses consumed per unit produced')
    position = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.product.name} x{self.quantity} (for {self.bom})"

    @property
    def qty_with_scrap(self):
        return float(self.quantity) * (1 + float(self.scrap_pct) / 100)


class WorkCenter(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='work_centers')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    capacity = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    capacity_uom = models.CharField(max_length=20, default='units/hour')
    cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class BOMOperation(models.Model):
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name='operations')
    work_center = models.ForeignKey(WorkCenter, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    sequence = models.IntegerField(default=10)
    duration_minutes = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['sequence']

    def __str__(self):
        return f"{self.name} (Step {self.sequence})"


# ── Footwear / Shoe BOM Extensions ───────────────────────────────────────────

class ShoeArticleBOM(models.Model):
    """BOM header per shoe article — one BOM per buyer order batch."""
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='shoe_article_boms')
    article_code = models.CharField(max_length=50, help_text="Links to PLM ShoeArticle.article_code")
    article_name = models.CharField(max_length=150, blank=True)
    last_code = models.CharField(max_length=50, blank=True)
    size_run = models.CharField(max_length=30, blank=True)
    sample_size = models.CharField(max_length=10, blank=True)
    buyer = models.CharField(max_length=150, blank=True)
    date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='shoe_boms_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"BOM: {self.article_code} — {self.buyer}"

    @property
    def total_pairs(self):
        return sum(c.total_pairs for c in self.colorways.all())

    @property
    def total_material_cost(self):
        return sum(
            float(l.total_price) for l in self.bom_lines.all()
            if l.total_price is not None
        )


class ShoeColorwayEntry(models.Model):
    """Per-colour size assortment for a ShoeArticleBOM."""
    bom = models.ForeignKey(ShoeArticleBOM, on_delete=models.CASCADE, related_name='colorways')
    leather_code = models.CharField(max_length=50, help_text="Colour name or leather code")
    size_data = models.JSONField(default=dict, help_text="Dict of size→qty e.g. {'35':2,'36':3,'37':3,'38':2,'39':2}")
    pairs_per_carton = models.PositiveIntegerField(default=12)
    sets = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['leather_code']

    def __str__(self):
        return f"{self.leather_code} — {self.total_pairs} pairs"

    @property
    def total_pairs(self):
        return self.sets * self.pairs_per_carton


class ShoeBOMLine(models.Model):
    """Per-material consumption line — covers upper, lining, footbed, adhesives, hardware."""
    CATEGORY = [
        ('upper', 'Upper'),
        ('lining', 'Lining'),
        ('footbed', 'Footbed'),
        ('adhesive', 'Adhesive & Chemical'),
        ('lasting', 'Lasting & Bottom'),
        ('finishing', 'Finishing'),
        ('other', 'Others'),
    ]

    bom = models.ForeignKey(ShoeArticleBOM, on_delete=models.CASCADE, related_name='bom_lines')
    colorway = models.ForeignKey(
        ShoeColorwayEntry, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='bom_lines', help_text="Blank = shared across all colours"
    )
    category = models.CharField(max_length=15, choices=CATEGORY, default='upper')
    material_name = models.CharField(max_length=150)
    uom = models.CharField(max_length=20, default='S/ft')
    cons_per_pair = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    order_qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_cons = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    conversion_note = models.CharField(max_length=100, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_pair = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ['category', 'position', 'material_name']

    def __str__(self):
        return f"{self.get_category_display()}: {self.material_name}"

    def save(self, *args, **kwargs):
        qty = float(self.order_qty or 0)
        if qty and self.cons_per_pair:
            self.total_cons = float(self.cons_per_pair) * qty
        if self.unit_price and self.cons_per_pair:
            self.price_per_pair = float(self.cons_per_pair) * float(self.unit_price)
            if qty:
                self.total_price = float(self.price_per_pair) * qty
        super().save(*args, **kwargs)
