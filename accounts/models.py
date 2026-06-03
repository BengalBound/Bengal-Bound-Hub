from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('super_admin', 'Super Admin'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
        ('contractor', 'Contractor'),
        ('auditor', 'Auditor (Read-Only)'),
        ('console_user', 'Console User'),
        ('affiliate', 'Affiliate'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='console_user')
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    firebase_uid = models.CharField(max_length=128, unique=True, blank=True, null=True)

    # Use email as the primary login field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    @property
    def is_workspace_user(self):
        return self.role in ['super_admin', 'manager', 'employee', 'contractor', 'auditor']

class WorkspaceProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='workspace_profile')
    title = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    joined_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - Workspace Profile"

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    company_name = models.CharField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - Customer Profile"
