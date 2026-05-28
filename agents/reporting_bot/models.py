from django.db import models
from hub.models import BusinessInstance


class ReportConfig(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="reportconfig_set")
    report_name = models.CharField(max_length=300)
    frequency = models.CharField(
        max_length=10,
        choices=[("weekly", "Weekly"), ("biweekly", "Biweekly"), ("monthly", "Monthly")],
    )
    send_day = models.CharField(max_length=20, default="monday")
    recipients = models.JSONField(default=list)
    data_sources = models.JSONField(default=list)
    kpis = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.report_name} [{self.frequency}]"


class Report(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="report_set")
    config = models.ForeignKey(ReportConfig, on_delete=models.CASCADE, related_name="reports")
    period_start = models.DateField()
    period_end = models.DateField()
    ai_narrative = models.TextField(blank=True)
    status = models.CharField(
        max_length=15,
        choices=[
            ("generating", "Generating"),
            ("ready", "Ready"),
            ("sent", "Sent"),
            ("failed", "Failed"),
        ],
        default="generating",
    )
    generated_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-period_end"]

    def __str__(self):
        return f"{self.config.report_name}: {self.period_start} → {self.period_end}"
