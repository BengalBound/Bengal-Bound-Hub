from django.db import models


class ExecTask(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="exectask_set")
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    source = models.CharField(max_length=50)
    priority = models.CharField(
        max_length=20,
        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")],
        default="medium",
    )
    status = models.CharField(
        max_length=20,
        choices=[("open", "Open"), ("in_progress", "In Progress"), ("done", "Done"), ("deferred", "Deferred")],
        default="open",
    )
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.priority}] {self.title}"


class MeetingBrief(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="meetingbrief_set")
    meeting_title = models.CharField(max_length=500)
    scheduled_at = models.DateTimeField()
    attendees = models.JSONField(default=list)
    agenda = models.TextField(blank=True)
    talking_points = models.JSONField(default=list)
    ai_briefing = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return self.meeting_title
