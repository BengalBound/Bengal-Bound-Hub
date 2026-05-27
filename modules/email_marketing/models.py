from django.db import models
from accounts.models import User


class EmailList(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='em_lists')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def subscriber_count(self):
        return self.subscribers.filter(is_subscribed=True).count()


class Subscriber(models.Model):
    STATUS = [('subscribed', 'Subscribed'), ('unsubscribed', 'Unsubscribed'), ('bounced', 'Bounced'), ('complained', 'Complained')]
    email_list = models.ForeignKey(EmailList, on_delete=models.CASCADE, related_name='subscribers')
    email = models.EmailField()
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    is_subscribed = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS, default='subscribed')
    custom_data = models.JSONField(default=dict, blank=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-subscribed_at']
        unique_together = [('email_list', 'email')]

    def __str__(self):
        return f"{self.email} ({self.email_list.name})"


class EmailTemplate(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='em_templates')
    name = models.CharField(max_length=200)
    subject = models.CharField(max_length=500)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='email_templates')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Campaign(models.Model):
    STATUS = [('draft', 'Draft'), ('scheduled', 'Scheduled'), ('sending', 'Sending'), ('sent', 'Sent'), ('paused', 'Paused'), ('cancelled', 'Cancelled')]
    TYPE = [('regular', 'Regular'), ('automated', 'Automated'), ('ab_test', 'A/B Test')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='em_campaigns')
    name = models.CharField(max_length=200)
    campaign_type = models.CharField(max_length=20, choices=TYPE, default='regular')
    subject = models.CharField(max_length=500)
    from_name = models.CharField(max_length=100, blank=True)
    from_email = models.EmailField(blank=True)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    email_list = models.ForeignKey(EmailList, on_delete=models.SET_NULL, null=True, related_name='campaigns')
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    total_sent = models.IntegerField(default=0)
    total_opened = models.IntegerField(default=0)
    total_clicked = models.IntegerField(default=0)
    total_bounced = models.IntegerField(default=0)
    total_unsubscribed = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_campaigns')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def open_rate(self):
        if self.total_sent:
            return round(self.total_opened / self.total_sent * 100, 1)
        return 0

    @property
    def click_rate(self):
        if self.total_sent:
            return round(self.total_clicked / self.total_sent * 100, 1)
        return 0
