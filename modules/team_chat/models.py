from django.db import models
from django.utils import timezone
from accounts.models import User


class Channel(models.Model):
    CHANNEL_TYPES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('announcement', 'Announcement'),
    ]
    business = models.ForeignKey(
        'bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='chat_channels'
    )
    name = models.CharField(max_length=80)
    topic = models.CharField(max_length=250, blank=True)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES, default='public')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_channels')
    created_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']
        unique_together = [('business', 'name')]

    def __str__(self):
        return f"#{self.name} ({self.business.name})"

    def last_message(self):
        return self.messages.order_by('-created_at').first()

    def unread_count(self, user):
        member = self.members.filter(user=user).first()
        if not member or not member.last_read_at:
            return self.messages.count()
        return self.messages.filter(created_at__gt=member.last_read_at).count()


class ChannelMember(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='channel_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)

    class Meta:
        unique_together = [('channel', 'user')]

    def mark_read(self):
        self.last_read_at = timezone.now()
        self.save(update_fields=['last_read_at'])


class Message(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='chat_messages')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='thread_replies')
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author} in #{self.channel.name}: {self.content[:50]}"

    def display_content(self):
        return '[deleted]' if self.is_deleted else self.content


class MessageReaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reactions')
    emoji = models.CharField(max_length=10)

    class Meta:
        unique_together = [('message', 'user', 'emoji')]

    def __str__(self):
        return f"{self.emoji} by {self.user.email} on msg {self.message_id}"


class DirectMessage(models.Model):
    business = models.ForeignKey(
        'bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='direct_messages'
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_dms')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_dms')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"DM {self.sender} → {self.recipient}"
