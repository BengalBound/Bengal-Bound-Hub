from django.db import models
from django.utils import timezone
from accounts.models import User


class Contact(models.Model):
    TYPE_CHOICES = [
        ('person', 'Person'),
        ('company', 'Company'),
    ]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='crm_contacts')
    contact_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='person')
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    mobile = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    tags = models.CharField(max_length=200, blank=True, help_text='Comma-separated')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_crm_contacts')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_crm_contacts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.contact_type == 'company':
            return self.company_name or 'Unnamed Company'
        return f"{self.first_name} {self.last_name}".strip() or self.email or 'Unnamed'

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.company_name or self.email


class Pipeline(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='crm_pipelines')
    name = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.business.name})"


class Stage(models.Model):
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='stages')
    name = models.CharField(max_length=100)
    position = models.IntegerField(default=0)
    probability = models.IntegerField(default=0, help_text='Win probability %')
    color = models.CharField(max_length=7, default='#3b82f6')
    is_won = models.BooleanField(default=False)
    is_lost = models.BooleanField(default=False)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.name} ({self.pipeline.name})"


class Deal(models.Model):
    PRIORITY = [('low', 'Low'), ('normal', 'Normal'), ('high', 'High')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='crm_deals')
    name = models.CharField(max_length=200)
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='deals')
    pipeline = models.ForeignKey(Pipeline, on_delete=models.SET_NULL, null=True, related_name='deals')
    stage = models.ForeignKey(Stage, on_delete=models.SET_NULL, null=True, related_name='deals')
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=5, default='USD')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='normal')
    expected_close = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_deals')
    description = models.TextField(blank=True)
    is_won = models.BooleanField(default=False)
    is_lost = models.BooleanField(default=False)
    lost_reason = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_deals')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def status(self):
        if self.is_won:
            return 'won'
        if self.is_lost:
            return 'lost'
        return 'open'


class Activity(models.Model):
    TYPE_CHOICES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('task', 'Task'),
        ('note', 'Note'),
        ('deadline', 'Deadline'),
    ]
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='crm_activities')
    activity_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='task')
    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='crm_activities')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_crm_activities')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return self.due_date and self.due_date < timezone.now() and self.status == 'planned'
