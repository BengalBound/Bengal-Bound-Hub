from django.db import models
from accounts.models import User


class DocumentFolder(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='doc_folders')
    name = models.CharField(max_length=200)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_folders')
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def path(self):
        parts = [self.name]
        parent = self.parent
        while parent:
            parts.insert(0, parent.name)
            parent = parent.parent
        return ' / '.join(parts)


class Document(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='documents')
    folder = models.ForeignKey(DocumentFolder, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='documents/files/')
    file_size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=300, blank=True, help_text='Comma-separated')
    version = models.CharField(max_length=20, default='1.0')
    is_template = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def file_size_display(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def extension(self):
        import os
        _, ext = os.path.splitext(self.name)
        return ext.lower()


class DocumentShare(models.Model):
    ACCESS = [('view', 'View'), ('edit', 'Edit'), ('download', 'Download')]
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='shares')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_documents')
    access_level = models.CharField(max_length=10, choices=ACCESS, default='view')
    shared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='document_shares_given')
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('document', 'shared_with')]

    def __str__(self):
        return f"{self.document} → {self.shared_with}"
