from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class CareClient(models.Model):
    CARE_LEVEL_CHOICES = [
        ('independent', 'Independent'),
        ('assisted', 'Assisted'),
        ('full_care', 'Full Care'),
        ('specialist', 'Specialist Care'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('discharged', 'Discharged'),
        ('inactive', 'Inactive'),
    ]
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='care_clients')
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField(null=True, blank=True)
    contact_name = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    care_level = models.CharField(max_length=20, choices=CARE_LEVEL_CHOICES, default='assisted')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    assigned_to = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='care_clients')
    admission_date = models.DateField(null=True, blank=True)
    medical_notes = models.TextField(blank=True)
    dietary_requirements = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class CarePlan(models.Model):
    CARE_TYPE_CHOICES = [
        ('personal', 'Personal Care'),
        ('medical', 'Medical'),
        ('social', 'Social / Activity'),
        ('dietary', 'Dietary'),
        ('mobility', 'Mobility & Exercise'),
        ('other', 'Other'),
    ]
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('twice_daily', 'Twice Daily'),
        ('weekly', 'Weekly'),
        ('fortnightly', 'Fortnightly'),
        ('monthly', 'Monthly'),
        ('as_needed', 'As Needed'),
    ]
    client = models.ForeignKey(CareClient, on_delete=models.CASCADE, related_name='care_plans')
    title = models.CharField(max_length=200)
    care_type = models.CharField(max_length=20, choices=CARE_TYPE_CHOICES, default='personal')
    description = models.TextField()
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    assigned_to = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_care_plans')
    start_date = models.DateField()
    review_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.full_name} – {self.title}"


class CareSession(models.Model):
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('missed', 'Missed'),
        ('cancelled', 'Cancelled'),
    ]
    client = models.ForeignKey(CareClient, on_delete=models.CASCADE, related_name='care_sessions')
    care_plan = models.ForeignKey(CarePlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    performed_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='care_sessions_performed')
    session_date = models.DateField()
    session_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.full_name} – {self.session_date}"


class StaffRota(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='care_rota_entries')
    employee = models.ForeignKey(BusinessEmployee, on_delete=models.CASCADE, related_name='care_rota_entries')
    shift_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    role = models.CharField(max_length=100, blank=True)
    notes = models.CharField(max_length=300, blank=True)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['shift_date', 'start_time']

    def __str__(self):
        return f"{self.employee} – {self.shift_date}"


class ComplianceDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('policy', 'Policy'),
        ('procedure', 'Procedure'),
        ('certificate', 'Certificate'),
        ('training_record', 'Training Record'),
        ('risk_assessment', 'Risk Assessment'),
        ('incident_report', 'Incident Report'),
        ('other', 'Other'),
    ]
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='compliance_documents')
    title = models.CharField(max_length=200)
    doc_type = models.CharField(max_length=30, choices=DOC_TYPE_CHOICES, default='policy')
    description = models.TextField(blank=True)
    file_url = models.URLField(blank=True)
    review_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='compliance_docs_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
