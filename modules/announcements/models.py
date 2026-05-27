from django.db import models
from django.utils import timezone
from accounts.models import User


class Announcement(models.Model):
    PRIORITY = [('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')]
    TYPE = [('general', 'General'), ('policy', 'Policy'), ('event', 'Event'), ('maintenance', 'Maintenance'), ('holiday', 'Holiday'), ('alert', 'Alert')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=300)
    content = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=TYPE, default='general')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='normal')
    target_departments = models.JSONField(default=list, blank=True, help_text='Empty = all departments')
    target_roles = models.JSONField(default=list, blank=True, help_text='Empty = all roles')
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    publish_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    allow_comments = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-publish_at']

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        return self.publish_at <= timezone.now() and self.is_active

    @property
    def is_expired(self):
        return self.expires_at and self.expires_at < timezone.now()


class AnnouncementRead(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='reads')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_announcements')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('announcement', 'user')]


class AnnouncementComment(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcement_comments')
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.announcement}"
