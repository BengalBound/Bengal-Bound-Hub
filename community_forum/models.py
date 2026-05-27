from django.db import models
from django.conf import settings

class ForumCategory(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-chat-dots', help_text="Bootstrap icon class")
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Forum Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class ForumTopic(models.Model):
    TOPIC_TYPES = (
        ('question', 'Question'),
        ('article', 'Article'),
        ('problem', 'Problem Report'),
    )
    category = models.ForeignKey(ForumCategory, on_delete=models.CASCADE, related_name='topics')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=255)
    content = models.TextField()
    topic_type = models.CharField(max_length=20, choices=TOPIC_TYPES, default='question')
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    is_solved = models.BooleanField(default=False, help_text="For Questions — mark when answered")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.get_topic_type_display()}] {self.title}"

class ForumPost(models.Model):
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, related_name='posts')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_posts')
    content = models.TextField()
    # AI Moderation fields
    is_flagged = models.BooleanField(default=False, help_text="Serea flagged this post")
    ai_flag_reason = models.TextField(blank=True, help_text="Reason Serea flagged this post")
    is_escalated = models.BooleanField(default=False, help_text="Escalated to Workspace Admin")
    is_hidden = models.BooleanField(default=False, help_text="Hidden from public view pending moderation")
    # Admin moderation
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='moderated_posts'
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        flagged = " [FLAGGED]" if self.is_flagged else ""
        return f"Post by {self.author.email} in '{self.topic.title}'{flagged}"

class ForumModerationLog(models.Model):
    """Audit trail for all moderation actions by Serea or Workspace Admins."""
    ACTION_CHOICES = (
        ('ai_flag', 'AI Flagged'),
        ('ai_escalate', 'AI Escalated to Admin'),
        ('admin_hide', 'Admin Hid Post'),
        ('admin_restore', 'Admin Restored Post'),
        ('admin_lock', 'Admin Locked Topic'),
        ('admin_pin', 'Admin Pinned Topic'),
        ('admin_mark_solved', 'Admin Marked Solved'),
    )
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='moderation_logs', null=True, blank=True)
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, related_name='moderation_logs', null=True, blank=True)
    actor = models.CharField(max_length=100, default='Serea AI')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_action_display()}] by {self.actor}"
