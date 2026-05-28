import uuid
from django.db import models

class Meeting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="scribe_meetings", null=True, blank=True)
    title = models.CharField(max_length=255)
    meeting_url = models.URLField(blank=True)
    
    # Provider integration (e.g., Recall.ai bot ID)
    bot_id = models.CharField(max_length=100, blank=True)
    platform = models.CharField(max_length=50, default="zoom")  # zoom, google_meet, teams
    
    # Meeting Data
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    raw_transcript = models.TextField(blank=True, help_text="Diarized transcript from the video provider")
    
    # AI Generated Outputs
    executive_summary = models.TextField(blank=True)
    sentiment = models.CharField(max_length=50, blank=True)
    
    # State
    status = models.CharField(
        max_length=20,
        choices=[
            ("scheduled", "Scheduled"),
            ("recording", "Recording"),
            ("processing", "Processing Transcript"),
            ("completed", "Completed"),
            ("failed", "Failed")
        ],
        default="scheduled"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.title} [{self.status}]"


class ActionItem(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="action_items")
    assignee_name = models.CharField(max_length=100, blank=True)
    task_description = models.TextField()
    is_completed = models.BooleanField(default=False)
    extracted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["extracted_at"]

    def __str__(self):
        return f"[{self.assignee_name}] {self.task_description[:50]}"
