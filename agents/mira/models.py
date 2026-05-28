from django.db import models

class ClientHealth(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="mira_client_healths")
    health_score = models.IntegerField()
    risk_level = models.CharField(
        max_length=10,
        choices=[("healthy", "Healthy"), ("at_risk", "At Risk"), ("critical", "Critical"), ("churned", "Churned")],
    )
    login_frequency = models.FloatField(default=0)
    feature_usage = models.FloatField(default=0)
    open_tickets = models.IntegerField(default=0)
    churn_probability = models.FloatField(null=True, blank=True)
    ai_summary = models.TextField(blank=True)
    checked_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-checked_at"]

    def __str__(self):
        return f"Health {self.health_score} [{self.risk_level}]"

class SuccessEmail(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="mira_success_emails")
    email_type = models.CharField(
        max_length=15,
        choices=[
            ("onboarding", "Onboarding"),
            ("checkin", "Check-In"),
            ("nps", "NPS"),
            ("renewal", "Renewal"),
            ("upsell", "Upsell"),
            ("intervention", "Intervention"),
        ],
    )
    subject = models.CharField(max_length=500)
    body = models.TextField()
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return f"[{self.email_type}] {self.subject}"
