import secrets
from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class ClientPortalAccess(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='client_portal_accesses')
    client_name = models.CharField(max_length=150)
    client_email = models.EmailField()
    deal_reference = models.CharField(max_length=200, blank=True, help_text='Property address or deal reference')
    token = models.CharField(max_length=64, unique=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_portal_accesses')
    created_at = models.DateTimeField(auto_now_add=True)
    welcome_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client_name} — {self.deal_reference}"

    @property
    def document_count(self):
        return self.documents.count()


class PortalDocument(models.Model):
    DOC_TYPES = [
        ('id', 'ID / Passport'),
        ('financial', 'Financial / Bank Statement'),
        ('contract', 'Contract / Agreement'),
        ('disclosure', 'Disclosure'),
        ('inspection', 'Inspection Report'),
        ('mortgage', 'Mortgage / Loan Docs'),
        ('other', 'Other'),
    ]
    SOURCE = [('agent', 'Shared by Agent'), ('client', 'Uploaded by Client')]

    access = models.ForeignKey(ClientPortalAccess, on_delete=models.CASCADE, related_name='documents')
    document_name = models.CharField(max_length=200)
    doc_type = models.CharField(max_length=12, choices=DOC_TYPES, default='other')
    source = models.CharField(max_length=8, choices=SOURCE, default='agent')
    file_url = models.URLField(blank=True, help_text='Link to document (Drive, Dropbox, etc.)')
    notes = models.TextField(blank=True)
    is_signed = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['doc_type', 'document_name']

    def __str__(self):
        return f"{self.document_name} — {self.access.client_name}"
