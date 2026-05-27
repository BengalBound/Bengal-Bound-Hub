from django.db import models
from django.utils import timezone
from accounts.models import User


class ContractTemplate(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='contract_templates')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True)
    content = models.TextField()
    variables = models.JSONField(default=list, blank=True, help_text='List of variable names used in the template')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_contract_templates')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Contract(models.Model):
    STATUS = [('draft', 'Draft'), ('sent', 'Sent'), ('viewed', 'Viewed'), ('signed', 'Signed'), ('expired', 'Expired'), ('cancelled', 'Cancelled'), ('rejected', 'Rejected')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='contracts')
    template = models.ForeignKey(ContractTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    reference = models.CharField(max_length=50, blank=True)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_contracts')
    valid_from = models.DateField(default=timezone.now)
    valid_until = models.DateField(null=True, blank=True)
    value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=5, default='USD')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        return self.valid_until and self.valid_until < timezone.now().date()


class ContractParty(models.Model):
    ROLE = [('sender', 'Sender'), ('signer', 'Signer'), ('cc', 'CC')]
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='parties')
    role = models.CharField(max_length=10, choices=ROLE, default='signer')
    name = models.CharField(max_length=200)
    email = models.EmailField()
    company = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=100, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    signature_data = models.TextField(blank=True, help_text='Base64 signature image or e-sign token')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['role', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_role_display()}) — {self.contract.title}"
