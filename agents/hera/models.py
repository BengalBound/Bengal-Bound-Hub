import uuid
from django.db import models
from django.conf import settings
from core.models import BaseModel


class PolicyCategory(models.TextChoices):
    ONBOARDING = "onboarding", "Onboarding"
    LEAVE      = "leave",      "Leave"
    BENEFITS   = "benefits",   "Benefits"
    CONDUCT    = "conduct",    "Conduct"
    PAYROLL    = "payroll",    "Payroll"
    OTHER      = "other",      "Other"


class PolicyQuery(BaseModel):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="policy_queries")
    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="policy_queries")
    question     = models.TextField()
    ai_answer    = models.TextField(blank=True)
    category     = models.CharField(max_length=20, choices=PolicyCategory.choices, default=PolicyCategory.OTHER)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.question[:80]


class OnboardingTask(BaseModel):
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization   = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="onboarding_tasks")
    employee_name  = models.CharField(max_length=255)
    employee_email = models.EmailField()
    task           = models.CharField(max_length=500)
    due_date       = models.DateField(null=True, blank=True)
    is_completed   = models.BooleanField(default=False)

    class Meta:
        ordering = ["due_date", "is_completed"]

    def __str__(self):
        return f"{self.employee_name} — {self.task}"
