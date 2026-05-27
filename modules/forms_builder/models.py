from django.db import models
from accounts.models import User


class HubForm(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='hub_forms')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    slug = models.CharField(max_length=100, unique=True, help_text="Public URL key")
    is_active = models.BooleanField(default=True)
    accepts_responses = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_forms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def response_count(self):
        return self.responses.count()


class HubFormField(models.Model):
    TYPES = [
        ('text', 'Short Text'),
        ('textarea', 'Long Text'),
        ('email', 'Email'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('select', 'Dropdown'),
        ('radio', 'Multiple Choice'),
        ('checkbox', 'Checkboxes'),
        ('file', 'File Upload'),
        ('rating', 'Star Rating'),
    ]

    form = models.ForeignKey(HubForm, on_delete=models.CASCADE, related_name='fields')
    label = models.CharField(max_length=300)
    field_type = models.CharField(max_length=20, choices=TYPES, default='text')
    placeholder = models.CharField(max_length=200, blank=True)
    help_text = models.CharField(max_length=300, blank=True)
    is_required = models.BooleanField(default=False)
    options = models.JSONField(default=list, blank=True, help_text="For select/radio/checkbox: ['Option 1', 'Option 2']")
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.form.title} / {self.label}"


class HubFormResponse(models.Model):
    form = models.ForeignKey(HubForm, on_delete=models.CASCADE, related_name='responses')
    respondent_email = models.EmailField(blank=True)
    respondent_name = models.CharField(max_length=200, blank=True)
    answers = models.JSONField(default=dict, help_text="field_id → value mapping")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Response to {self.form.title} at {self.submitted_at}"
