from django.db import models
from accounts.models import User


class AssistantConversation(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='assistant_conversations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assistant_conversations')
    title = models.CharField(max_length=200, blank=True)
    context_module = models.CharField(max_length=50, blank=True, help_text='Which module this conversation is about')
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title or f"Conversation #{self.pk}"

    def message_count(self):
        return self.messages.count()


class AssistantMessage(models.Model):
    ROLE = [('user', 'User'), ('assistant', 'Assistant'), ('system', 'System')]
    conversation = models.ForeignKey(AssistantConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE)
    content = models.TextField()
    tokens_used = models.IntegerField(default=0)
    model_used = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:100]}"


class AssistantPromptTemplate(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='assistant_prompt_templates')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    prompt = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    module = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_prompts')
    created_at = models.DateTimeField(auto_now_add=True)
    use_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name
