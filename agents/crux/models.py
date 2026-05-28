from django.db import models

class Contact(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="crux_contacts")
    crm_id = models.CharField(max_length=200, blank=True)
    name = models.CharField(max_length=300)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    company = models.CharField(max_length=300, blank=True)
    intent_score = models.IntegerField(null=True, blank=True)
    pipeline_stage = models.CharField(max_length=100, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    is_cold = models.BooleanField(default=False)
    ai_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.company})"

class Interaction(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="crux_interactions")
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name="interactions")
    interaction_type = models.CharField(
        max_length=20,
        choices=[
            ("email", "Email"),
            ("call", "Call"),
            ("meeting", "Meeting"),
            ("whatsapp", "WhatsApp"),
            ("note", "Note"),
        ],
    )
    summary = models.TextField()
    sentiment = models.CharField(
        max_length=10,
        choices=[("positive", "Positive"), ("neutral", "Neutral"), ("negative", "Negative")],
        blank=True,
    )
    occurred_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.interaction_type} with {self.contact.name}"
