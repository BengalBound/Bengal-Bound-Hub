from django.db import models


class DocumentationProject(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="documentationproject_set")
    name = models.CharField(max_length=300)
    doc_type = models.CharField(
        max_length=20,
        choices=[
            ("api", "API"),
            ("user_manual", "User Manual"),
            ("sop", "SOP"),
            ("wiki", "Wiki"),
            ("changelog", "Changelog"),
            ("code_docs", "Code Docs"),
        ],
    )
    repo_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    last_generated = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} [{self.doc_type}]"


class DocPage(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="docpage_set")
    project = models.ForeignKey(DocumentationProject, on_delete=models.CASCADE, related_name="pages")
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=300)
    content = models.TextField()
    section = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=10,
        choices=[("draft", "Draft"), ("published", "Published"), ("outdated", "Outdated"), ("archived", "Archived")],
        default="draft",
    )
    ai_generated = models.BooleanField(default=True)
    word_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
