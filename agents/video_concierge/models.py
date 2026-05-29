import uuid
from django.db import models

class VideoSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="video_sessions", null=True, blank=True)
    client_name = models.CharField(max_length=200, blank=True)

    # Meeting Context
    session_type = models.CharField(
        max_length=50,
        choices=[
            ("support", "Customer Support"),
            ("onboarding", "Client Onboarding"),
            ("sales", "Sales Qualification")
        ],
        default="support"
    )

    # WebRTC/Avatar Engine Context
    session_id = models.CharField(max_length=150, unique=True, help_text="HeyGen/D-ID Session ID")
    webrtc_sdp = models.TextField(blank=True, help_text="Session Description Protocol payload")

    # Metrics
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)

    # Outcomes
    resolution_status = models.CharField(
        max_length=50,
        choices=[
            ("resolved", "Resolved"),
            ("escalated", "Escalated to Human"),
            ("pending", "Pending Follow-up")
        ],
        default="resolved"
    )
    transcript = models.TextField(blank=True)
    ai_summary = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"VideoSession [{self.session_type}] - {self.client_name}"
