from django.db import models


class ITTicket(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="itticket_set")
    submitted_by = models.CharField(max_length=300)
    title = models.CharField(max_length=500)
    description = models.TextField()
    category = models.CharField(
        max_length=10,
        choices=[
            ("hardware", "Hardware"),
            ("software", "Software"),
            ("network", "Network"),
            ("access", "Access"),
            ("email", "Email"),
            ("other", "Other"),
        ],
    )
    priority = models.CharField(
        max_length=10,
        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")],
        default="medium",
    )
    status = models.CharField(
        max_length=15,
        choices=[
            ("open", "Open"),
            ("ai_resolving", "AI Resolving"),
            ("escalated", "Escalated"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
        ],
        default="open",
    )
    ai_solution = models.TextField(blank=True)
    ai_confidence = models.FloatField(null=True, blank=True)
    sla_hours = models.IntegerField(default=4)
    sla_breached = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.priority}] {self.title}"


class KnowledgeArticle(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="knowledgearticle_set")
    title = models.CharField(max_length=500)
    category = models.CharField(max_length=20)
    problem = models.TextField()
    solution = models.TextField()
    success_count = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-success_count"]

    def __str__(self):
        return self.title
