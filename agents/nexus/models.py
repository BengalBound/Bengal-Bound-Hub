from django.db import models
from hub.models import BusinessInstance


class Course(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="course_set")
    title = models.CharField(max_length=500)
    course_type = models.CharField(
        max_length=15,
        choices=[
            ("onboarding", "Onboarding"),
            ("technical", "Technical"),
            ("compliance", "Compliance"),
            ("soft_skills", "Soft Skills"),
        ],
    )
    description = models.TextField()
    modules = models.JSONField(default=list)
    duration_hours = models.FloatField(default=1.0)
    is_mandatory = models.BooleanField(default=False)
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="enrollment_set")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    employee_name = models.CharField(max_length=300)
    employee_email = models.EmailField()
    status = models.CharField(
        max_length=15,
        choices=[
            ("assigned", "Assigned"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("overdue", "Overdue"),
        ],
        default="assigned",
    )
    progress_pct = models.IntegerField(default=0)
    quiz_score = models.FloatField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.employee_name} → {self.course.title}"
