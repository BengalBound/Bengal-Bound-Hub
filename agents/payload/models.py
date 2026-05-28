from django.db import models
from hub.models import BusinessInstance


class Vendor(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="vendor_set")
    name = models.CharField(max_length=300)
    category = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=300)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=100, blank=True)
    payment_terms = models.CharField(max_length=100, blank=True)
    performance_score = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=15,
        choices=[("active", "Active"), ("on_hold", "On Hold"), ("blacklisted", "Blacklisted")],
        default="active",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class RFQ(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="rfq_set")
    title = models.CharField(max_length=500)
    description = models.TextField()
    requirements = models.JSONField(default=list)
    deadline = models.DateTimeField()
    status = models.CharField(
        max_length=15,
        choices=[
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("responses_in", "Responses In"),
            ("evaluated", "Evaluated"),
            ("awarded", "Awarded"),
        ],
        default="draft",
    )
    ai_recommendation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
