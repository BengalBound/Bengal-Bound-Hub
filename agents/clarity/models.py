from django.db import models
from hub.models import BusinessInstance


class FeedbackSurvey(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="feedbacksurvey_set")
    name = models.CharField(max_length=300)
    survey_type = models.CharField(
        max_length=20,
        choices=[
            ("in_app", "In-App"),
            ("post_session", "Post Session"),
            ("nps", "NPS"),
            ("feature", "Feature"),
            ("exit", "Exit"),
        ],
    )
    questions = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    responses_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} [{self.survey_type}]"


class InsightTheme(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="insighttheme_set")
    theme = models.CharField(max_length=300)
    theme_type = models.CharField(
        max_length=20,
        choices=[
            ("pain_point", "Pain Point"),
            ("feature_request", "Feature Request"),
            ("praise", "Praise"),
            ("confusion", "Confusion"),
        ],
    )
    mention_count = models.IntegerField(default=1)
    priority_score = models.IntegerField(null=True, blank=True)
    example_quotes = models.JSONField(default=list)
    ai_analysis = models.TextField(blank=True)
    first_seen = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-mention_count"]

    def __str__(self):
        return f"{self.theme} [{self.theme_type}]"
