from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class DataForm(models.Model):
    FORM_TYPE_CHOICES = [
        ('survey', 'Survey'),
        ('poll', 'Poll'),
        ('feedback', 'Feedback Form'),
        ('intake', 'Client Intake'),
        ('inspection', 'Inspection Checklist'),
        ('registration', 'Registration Form'),
        ('other', 'Other'),
    ]
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='data_forms')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    form_type = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES, default='survey')
    is_active = models.BooleanField(default=True)
    is_anonymous = models.BooleanField(default=False)
    created_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_data_forms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def response_count(self):
        return self.responses.count()

    def __str__(self):
        return self.title


class FormField(models.Model):
    FIELD_TYPE_CHOICES = [
        ('text', 'Short Text'),
        ('textarea', 'Long Text'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('select', 'Dropdown'),
        ('checkbox', 'Checkboxes'),
        ('radio', 'Multiple Choice'),
        ('rating', 'Rating (1–5)'),
        ('yes_no', 'Yes / No'),
    ]
    form = models.ForeignKey(DataForm, on_delete=models.CASCADE, related_name='fields')
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES, default='text')
    label = models.CharField(max_length=300)
    placeholder = models.CharField(max_length=200, blank=True)
    options = models.TextField(blank=True, help_text='Comma-separated options for select/radio/checkbox')
    is_required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def options_list(self):
        return [o.strip() for o in self.options.split(',') if o.strip()]

    def __str__(self):
        return f"{self.form.title} – {self.label}"


class FormResponse(models.Model):
    form = models.ForeignKey(DataForm, on_delete=models.CASCADE, related_name='responses')
    respondent_name = models.CharField(max_length=200, blank=True)
    respondent_email = models.EmailField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.form.title} – {self.submitted_at:%d %b %Y %H:%M}"


class FieldResponse(models.Model):
    form_response = models.ForeignKey(FormResponse, on_delete=models.CASCADE, related_name='field_responses')
    field = models.ForeignKey(FormField, on_delete=models.CASCADE, related_name='field_answers')
    value = models.TextField(blank=True)

    def __str__(self):
        return f"{self.field.label}: {self.value[:50]}"
