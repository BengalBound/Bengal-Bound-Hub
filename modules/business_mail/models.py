from django.db import models
from accounts.models import User


class MailAccount(models.Model):
    """A business email account, e.g. info@acmecorp.com"""
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='mail_accounts')
    address = models.CharField(max_length=200, unique=True, help_text="Full email address: info@yourdomain.com")
    display_name = models.CharField(max_length=100, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='mail_accounts')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['address']

    def __str__(self):
        return self.address


class MailMessage(models.Model):
    FOLDERS = [
        ('inbox', 'Inbox'),
        ('sent', 'Sent'),
        ('drafts', 'Drafts'),
        ('trash', 'Trash'),
        ('spam', 'Spam'),
    ]

    account = models.ForeignKey(MailAccount, on_delete=models.CASCADE, related_name='messages')
    folder = models.CharField(max_length=20, choices=FOLDERS, default='inbox')
    from_address = models.CharField(max_length=200)
    to_addresses = models.JSONField(default=list, help_text="List of recipient addresses")
    cc_addresses = models.JSONField(default=list, blank=True)
    subject = models.CharField(max_length=500, blank=True)
    body_html = models.TextField(blank=True)
    body_text = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)
    thread_id = models.CharField(max_length=100, blank=True, db_index=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-received_at']

    def __str__(self):
        return f"[{self.folder}] {self.subject or '(no subject)'} — {self.from_address}"


class MailAttachment(models.Model):
    message = models.ForeignKey(MailMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='business_mail/attachments/')
    filename = models.CharField(max_length=255)
    size_bytes = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename
