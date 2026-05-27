from django.db import models
from django.utils import timezone
from accounts.models import User


class LeadSource(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='lead_sources')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Lead(models.Model):
    STATUS = [('new', 'New'), ('contacted', 'Contacted'), ('qualified', 'Qualified'), ('proposal', 'Proposal Sent'), ('negotiation', 'Negotiation'), ('won', 'Won'), ('lost', 'Lost'), ('unqualified', 'Unqualified')]
    PRIORITY = [('low', 'Low'), ('normal', 'Normal'), ('high', 'High')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='leads')
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    source = models.ForeignKey(LeadSource, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    status = models.CharField(max_length=20, choices=STATUS, default='new')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='normal')
    estimated_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=5, default='USD')
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    tags = models.CharField(max_length=300, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_leads')
    expected_close = models.DateField(null=True, blank=True)
    lost_reason = models.CharField(max_length=200, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.company or self.email or 'Lead'

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class LeadActivity(models.Model):
    TYPE = [('call', 'Call'), ('email', 'Email'), ('meeting', 'Meeting'), ('note', 'Note'), ('task', 'Task')]
    STATUS = [('planned', 'Planned'), ('done', 'Done'), ('cancelled', 'Cancelled')]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=TYPE, default='note')
    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='planned')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='lead_activities')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.lead}"
