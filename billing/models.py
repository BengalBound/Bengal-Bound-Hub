from django.db import models
from hub.models import BusinessInstance

class StripeCustomer(models.Model):
    business = models.OneToOneField(BusinessInstance, on_delete=models.CASCADE, related_name='stripe_customer')
    stripe_customer_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.business.name} - {self.stripe_customer_id}"

class BillingEvent(models.Model):
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=255)
    payload = models.JSONField(help_text="Full JSON payload from Stripe")
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} - {self.event_id}"
