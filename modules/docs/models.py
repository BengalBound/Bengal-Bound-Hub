from django.db import models
from accounts.models import User


class HubDoc(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='hub_docs')
    title = models.CharField(max_length=300, default='Untitled Document')
    content = models.TextField(blank=True, help_text="HTML content from the editor")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_docs')
    last_edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_docs')
    is_shared = models.BooleanField(default=False)
    is_template = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class DocShare(models.Model):
    ACCESS = [('view', 'View'), ('edit', 'Edit')]
    doc = models.ForeignKey(HubDoc, on_delete=models.CASCADE, related_name='shares')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_docs')
    access_level = models.CharField(max_length=10, choices=ACCESS, default='view')
    shared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='docs_shared_by_me')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('doc', 'shared_with')]

    def __str__(self):
        return f"{self.doc.title} → {self.shared_with.email}"
