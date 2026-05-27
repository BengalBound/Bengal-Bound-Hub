from django.db import models
from accounts.models import User


class DriveFolder(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='drive_folders')
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_drive_folders')
    color = models.CharField(max_length=30, default='#c084fc')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def path(self):
        parts = [self.name]
        p = self.parent
        while p:
            parts.insert(0, p.name)
            p = p.parent
        return ' / '.join(parts)


class DriveFile(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='drive_files')
    folder = models.ForeignKey(DriveFolder, on_delete=models.SET_NULL, null=True, blank=True, related_name='files')
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='cloud_drive/files/')
    size_bytes = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    tags = models.CharField(max_length=300, blank=True)
    is_starred = models.BooleanField(default=False)
    is_trashed = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_drive_files')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def size_display(self):
        size = self.size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def extension(self):
        import os
        _, ext = os.path.splitext(self.name)
        return ext.lower().lstrip('.')

    @property
    def icon_class(self):
        ext_map = {
            'pdf': 'bi-file-earmark-pdf',
            'doc': 'bi-file-earmark-word', 'docx': 'bi-file-earmark-word',
            'xls': 'bi-file-earmark-excel', 'xlsx': 'bi-file-earmark-excel',
            'ppt': 'bi-file-earmark-ppt', 'pptx': 'bi-file-earmark-ppt',
            'jpg': 'bi-file-earmark-image', 'jpeg': 'bi-file-earmark-image',
            'png': 'bi-file-earmark-image', 'gif': 'bi-file-earmark-image',
            'mp4': 'bi-file-earmark-play', 'mov': 'bi-file-earmark-play',
            'zip': 'bi-file-earmark-zip', 'rar': 'bi-file-earmark-zip',
            'txt': 'bi-file-earmark-text', 'csv': 'bi-file-earmark-spreadsheet',
        }
        return ext_map.get(self.extension, 'bi-file-earmark')


class DriveShare(models.Model):
    ACCESS = [('view', 'View'), ('edit', 'Edit'), ('download', 'Download')]
    file = models.ForeignKey(DriveFile, on_delete=models.CASCADE, related_name='shares')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drive_shares')
    access_level = models.CharField(max_length=10, choices=ACCESS, default='view')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('file', 'shared_with')]
