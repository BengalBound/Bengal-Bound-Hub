from django.db import models
from django.utils import timezone


class Product(models.Model):
    STAGES = [
        ('concept', 'Concept'), ('design', 'Design'), ('prototype', 'Prototype'),
        ('testing', 'Testing'), ('production', 'In Production'), ('eol', 'End of Life'),
        ('obsolete', 'Obsolete'),
    ]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='plm_products')
    product_code = models.CharField(max_length=50)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=80, blank=True)
    stage = models.CharField(max_length=20, choices=STAGES, default='concept')
    version = models.CharField(max_length=20, default='1.0')
    revision = models.PositiveSmallIntegerField(default=0)
    owner = models.ForeignKey('bredbound.BusinessEmployee', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('business', 'product_code')]
        ordering = ['name']

    def __str__(self):
        return f"{self.product_code} — {self.name} v{self.version}"


class BillOfMaterials(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='boms')
    bom_number = models.CharField(max_length=30)
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField(default=timezone.localdate)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-effective_date']

    def __str__(self):
        return f"BOM-{self.bom_number} for {self.product}"


class BOMLine(models.Model):
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name='lines')
    item_code = models.CharField(max_length=50)
    item_name = models.CharField(max_length=150)
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    unit = models.CharField(max_length=20, default='pcs')
    reference_designator = models.CharField(max_length=50, blank=True)
    is_substitute = models.BooleanField(default=False)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['item_code']

    def __str__(self):
        return f"{self.item_code} × {self.quantity} {self.unit}"


class EngineeringChangeOrder(models.Model):
    STATUS = [
        ('draft', 'Draft'), ('submitted', 'Submitted'), ('under_review', 'Under Review'),
        ('approved', 'Approved'), ('rejected', 'Rejected'), ('implemented', 'Implemented'),
    ]
    PRIORITY = [('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('critical', 'Critical')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='plm_ecos')
    eco_number = models.CharField(max_length=30)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ecos')
    title = models.CharField(max_length=200)
    reason = models.TextField()
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='normal')
    requested_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='requested_ecos')
    reviewed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_ecos')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('business', 'eco_number')]
        ordering = ['-created_at']

    def __str__(self):
        return f"ECO-{self.eco_number}: {self.title}"


class ProductDocument(models.Model):
    TYPES = [
        ('drawing', 'Technical Drawing'), ('spec', 'Specification'), ('sop', 'SOP'),
        ('test_report', 'Test Report'), ('certification', 'Certification'),
        ('user_manual', 'User Manual'), ('other', 'Other'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=20, choices=TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='plm/docs/', null=True, blank=True)
    version = models.CharField(max_length=20, default='1.0')
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.get_doc_type_display()}: {self.title}"


class ProductStage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stage_history')
    from_stage = models.CharField(max_length=20)
    to_stage = models.CharField(max_length=20)
    changed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-changed_at']


# ── Footwear / Shoe Manufacturing Extensions ──────────────────────────────────

class ShoeArticle(models.Model):
    LIFECYCLE = [
        ('development', 'Development'),
        ('active', 'Active'),
        ('run_out', 'Run-out'),
        ('archived', 'Archived'),
    ]
    CATEGORY = [
        ('sneakers', 'Sneakers'),
        ('sandals', 'Sandals'),
        ('ladies_heels', 'Ladies Heels'),
        ('oxfords', 'Formal Oxfords'),
        ('loafers', 'Penny Loafers'),
        ('boots', 'Boots'),
        ('other', 'Other'),
    ]
    CONSTRUCTION = [
        ('cemented', 'Cemented'),
        ('strobel', 'Cup-sole / Strobel'),
        ('goodyear', 'Goodyear Welted'),
        ('moccasin', 'Moccasin / Hand-stitched'),
        ('blake', 'Blake Stitched'),
        ('slip_lasted', 'Slip Lasted'),
        ('other', 'Other'),
    ]
    GENDER = [('M', 'Men'), ('W', 'Women'), ('U', 'Unisex'), ('K', 'Kids')]
    TIER = [
        ('hero', 'Hero'), ('core', 'Core'), ('entry', 'Entry'),
        ('promo', 'Promo'), ('private_label', 'Private Label'),
    ]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='shoe_articles')
    article_code = models.CharField(max_length=50, help_text="Design master code e.g. OX-001")
    sku_code = models.CharField(max_length=60, blank=True, help_text="Full SKU per CC-SS-MM-CL-GG-NN convention")
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=CATEGORY, default='other')
    construction = models.CharField(max_length=20, choices=CONSTRUCTION, default='cemented')
    gender = models.CharField(max_length=1, choices=GENDER, default='U')
    tier = models.CharField(max_length=15, choices=TIER, default='core')
    last_code = models.CharField(max_length=50, blank=True)
    size_run = models.CharField(max_length=30, blank=True, help_text="e.g. 39–45 (EU)")
    sample_size = models.CharField(max_length=10, blank=True)
    lifecycle = models.CharField(max_length=15, choices=LIFECYCLE, default='development')
    ex_factory_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=5, default='USD')
    moq = models.PositiveIntegerField(null=True, blank=True, help_text="MOQ per style")
    moq_per_colour = models.PositiveIntegerField(null=True, blank=True)
    pattern_ready = models.BooleanField(default=False)
    grading_done = models.BooleanField(default=False)
    sample_approved = models.BooleanField(default=False)
    costed_bom_ref = models.CharField(max_length=100, blank=True)
    image_ref = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    owner = models.ForeignKey('bredbound.BusinessEmployee', on_delete=models.SET_NULL, null=True, blank=True, related_name='shoe_articles_owned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('business', 'article_code')]
        ordering = ['category', 'article_code']

    def __str__(self):
        return f"{self.article_code} — {self.name}"

    @property
    def pending_actions(self):
        actions = []
        if not self.pattern_ready:
            actions.append('Pattern')
        if not self.grading_done:
            actions.append('Grading')
        if not self.sample_approved:
            actions.append('Sample Approval')
        return actions


class SampleOrder(models.Model):
    STAGE = [
        ('proto', 'Proto Sample'),
        ('fit', 'Fit Sample'),
        ('salesman', 'Salesman Sample'),
        ('pp', 'Pre-Production (PP)'),
        ('shipment', 'Shipment Sample'),
    ]
    STATUS = [
        ('pending', 'Pending'), ('in_progress', 'In Progress'),
        ('sent', 'Sent'), ('approved', 'Approved'), ('rejected', 'Rejected'),
    ]

    article = models.ForeignKey(ShoeArticle, on_delete=models.CASCADE, related_name='sample_orders')
    sdo_number = models.CharField(max_length=30)
    stage = models.CharField(max_length=15, choices=STAGE)
    status = models.CharField(max_length=15, choices=STATUS, default='pending')
    buyer = models.CharField(max_length=150, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    size_set = models.CharField(max_length=50, blank=True)
    material_colour_spec = models.CharField(max_length=200, blank=True)
    tech_pack_ref = models.CharField(max_length=100, blank=True)
    target_date = models.DateField(null=True, blank=True)
    actual_date = models.DateField(null=True, blank=True)
    is_charged = models.BooleanField(default=False)
    sample_charge = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    special_instructions = models.TextField(blank=True)
    raised_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='raised_sdos')
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_sdos')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('article', 'sdo_number')]
        ordering = ['-created_at']

    def __str__(self):
        return f"SDO-{self.sdo_number}: {self.article.article_code} ({self.get_stage_display()})"


class SampleBuyerComment(models.Model):
    ASPECTS = [
        ('last_fitting', 'Last Fitting'),
        ('upper_construction', 'Upper Construction'),
        ('stitch_density', 'Stitch Density'),
        ('sole_bonding', 'Sole Bonding'),
        ('finishing', 'Finishing & Polish'),
        ('branding', 'Branding'),
        ('packaging', 'Packaging'),
        ('overall_appearance', 'Overall Appearance'),
    ]

    sample_order = models.ForeignKey(SampleOrder, on_delete=models.CASCADE, related_name='buyer_comments')
    aspect = models.CharField(max_length=30, choices=ASPECTS)
    comment = models.TextField(blank=True)
    action_required = models.TextField(blank=True)
    owner_status = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.get_aspect_display()} — SDO {self.sample_order.sdo_number}"
