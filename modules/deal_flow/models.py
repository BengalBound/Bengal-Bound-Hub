from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class Deal(models.Model):
    DEAL_TYPES = [
        ('purchase', 'Purchase / Buy Side'),
        ('sale', 'Sale / List Side'),
        ('lease', 'Lease / Rental'),
        ('referral', 'Referral'),
        ('dual', 'Dual Agency'),
    ]
    STAGES = [
        ('prospect', 'Prospect'),
        ('offer', 'Offer Made'),
        ('under_contract', 'Under Contract'),
        ('inspection', 'Inspection'),
        ('appraisal', 'Appraisal'),
        ('financing', 'Financing / Mortgage'),
        ('closing', 'Closing'),
        ('closed', 'Closed / Won'),
        ('dead', 'Dead / Lost'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='deals')
    title = models.CharField(max_length=200)
    property_address = models.TextField()
    client_name = models.CharField(max_length=150)
    client_email = models.EmailField(blank=True)
    client_phone = models.CharField(max_length=30, blank=True)
    deal_type = models.CharField(max_length=10, choices=DEAL_TYPES, default='purchase')
    stage = models.CharField(max_length=20, choices=STAGES, default='prospect')
    assigned_agent = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_deals')
    listing_price = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    offer_price = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    commission_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Commission %')
    expected_close_date = models.DateField(null=True, blank=True)
    actual_close_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    broker_approved = models.BooleanField(default=False)
    broker_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} — {self.client_name}"

    @property
    def gross_commission(self):
        if self.offer_price and self.commission_pct:
            return round(self.offer_price * self.commission_pct / 100, 2)
        return None

    STAGE_ORDER = ['prospect', 'offer', 'under_contract', 'inspection', 'appraisal', 'financing', 'closing', 'closed', 'dead']

    @property
    def stage_index(self):
        try:
            return self.STAGE_ORDER.index(self.stage)
        except ValueError:
            return 0


class DealDocument(models.Model):
    DOC_STATUS = [
        ('pending', 'Pending Upload'),
        ('uploaded', 'Uploaded'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected / Needs Revision'),
    ]

    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='documents')
    document_name = models.CharField(max_length=200)
    is_required = models.BooleanField(default=True)
    status = models.CharField(max_length=10, choices=DOC_STATUS, default='pending')
    file_url = models.URLField(blank=True)
    uploaded_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_deal_docs')
    uploaded_at = models.DateTimeField(null=True, blank=True)
    notes = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['is_required', 'document_name']

    def __str__(self):
        return f"{self.deal.title} — {self.document_name}"


class DealNote(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='deal_notes')
    content = models.TextField()
    created_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='deal_notes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class DealMilestone(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=150)
    due_date = models.DateField(null=True, blank=True)
    is_done = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['is_done', 'due_date']
