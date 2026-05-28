from django.db import models


class Website(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="website_set")
    domain = models.URLField()
    cms = models.CharField(max_length=50, blank=True)
    last_crawled = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.domain


class SEOIssue(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="seoissue_set")
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name="issues")
    issue_type = models.CharField(
        max_length=20,
        choices=[
            ("missing_meta", "Missing Meta"),
            ("broken_link", "Broken Link"),
            ("duplicate_content", "Duplicate Content"),
            ("slow_page", "Slow Page"),
            ("missing_schema", "Missing Schema"),
            ("mobile_issue", "Mobile Issue"),
            ("missing_alt", "Missing Alt"),
        ],
    )
    severity = models.CharField(
        max_length=10,
        choices=[("critical", "Critical"), ("warning", "Warning"), ("info", "Info")],
    )
    page_url = models.URLField()
    description = models.TextField()
    fix_suggestion = models.TextField(blank=True)
    status = models.CharField(
        max_length=10,
        choices=[("open", "Open"), ("fixed", "Fixed"), ("ignored", "Ignored")],
        default="open",
    )
    found_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-found_at"]

    def __str__(self):
        return f"[{self.severity}] {self.issue_type} — {self.page_url}"
