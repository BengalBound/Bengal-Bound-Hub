from django.db import models


class LegalDocument(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="legaldocument_set")
    name = models.CharField(max_length=500)
    document_type = models.CharField(
        max_length=15,
        choices=[
            ("nda", "NDA"),
            ("contract", "Contract"),
            ("employment", "Employment"),
            ("vendor", "Vendor"),
            ("compliance", "Compliance"),
            ("other", "Other"),
        ],
    )
    raw_text = models.TextField(blank=True)
    overall_risk = models.IntegerField(null=True, blank=True)
    risk_label = models.CharField(
        max_length=10,
        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")],
        blank=True,
    )
    executive_summary = models.TextField(blank=True)
    status = models.CharField(
        max_length=10,
        choices=[
            ("queued", "Queued"),
            ("reviewing", "Reviewing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="queued",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.name} [{self.document_type}]"


class Clause(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="clause_set")
    document = models.ForeignKey(LegalDocument, on_delete=models.CASCADE, related_name="clauses")
    clause_number = models.CharField(max_length=50, blank=True)
    clause_title = models.CharField(max_length=500, blank=True)
    original_text = models.TextField()
    plain_english = models.TextField(blank=True)
    risk_level = models.CharField(
        max_length=10,
        choices=[("safe", "Safe"), ("caution", "Caution"), ("risky", "Risky"), ("critical", "Critical")],
        default="safe",
    )
    risk_score = models.IntegerField(default=0)
    negotiation_suggestion = models.TextField(blank=True)

    class Meta:
        ordering = ["clause_number"]

    def __str__(self):
        return f"Clause {self.clause_number}: {self.clause_title}"
