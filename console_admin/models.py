from django.db import models
from django.conf import settings
from encrypted_model_fields.fields import EncryptedCharField
from workspace_admin.models import HiredAIEmployee

class WorkspaceEnvironment(models.Model):
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workspaces')
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.client.email})"

class WorkspaceProject(models.Model):
    STATUS_CHOICES = (
        ('design', 'Design'),
        ('development', 'Development'),
        ('testing', 'Testing'),
        ('live', 'Live'),
        ('paused', 'Paused'),
    )
    PROJECT_TYPES = (
        ('web', 'Web'),
        ('mobile', 'Mobile'),
        ('software', 'Software'),
        ('api', 'API / Integration'),
        ('other', 'Other'),
    )
    workspace = models.ForeignKey(WorkspaceEnvironment, on_delete=models.CASCADE, related_name='projects', null=True)
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='design')
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES, default='web')
    domain = models.CharField(max_length=255, blank=True, null=True, help_text="Production domain for this project")
    api_key = models.CharField(max_length=255, blank=True, null=True, help_text="API key for data syncing between this project and BengalBound")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} [{self.get_status_display()}] ({self.client.email})"

class AITask(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    )
    project = models.ForeignKey(WorkspaceProject, on_delete=models.CASCADE, related_name='tasks')
    assigned_ai = models.ForeignKey(HiredAIEmployee, on_delete=models.CASCADE, related_name='assigned_tasks')
    title = models.CharField(max_length=255)
    instructions = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"[{self.status}] {self.title}"

class AIChatInteraction(models.Model):
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ai_employee = models.ForeignKey(HiredAIEmployee, on_delete=models.CASCADE)
    message_content = models.TextField()
    is_from_ai = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sender = self.ai_employee.ai_name if self.is_from_ai else self.client.email
        return f"{sender}: {self.message_content[:30]}..."

class SupportTicket(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved')
    )
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket #{self.id}: {self.subject}"

class AICredential(models.Model):
    """Stores API keys or credentials needed for the AI employee to use external tools."""
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ai_employee = models.ForeignKey(HiredAIEmployee, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=100)
    api_key_or_token = EncryptedCharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_name} Credential for {self.ai_employee.ai_name}"

class AITrainingDocument(models.Model):
    """
    Documents/instructions uploaded by a client to train their specific AI agent.
    These are passed to the n8n workflow as context for Serea's responses.
    """
    DOCUMENT_TYPES = (
        ('instruction', 'Custom Instruction'),
        ('faq', 'FAQ Document'),
        ('product_info', 'Product/Service Info'),
        ('tone_guide', 'Tone & Voice Guide'),
        ('other', 'Other'),
    )
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='training_docs')
    ai_employee = models.ForeignKey('workspace_admin.HiredAIEmployee', on_delete=models.CASCADE, related_name='training_docs')
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='instruction')
    content = models.TextField(help_text="Paste training content or instructions here")
    is_active = models.BooleanField(default=True, help_text="Only active documents are passed to the AI")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.get_document_type_display()}] {self.title} → {self.ai_employee.ai_name}"

class AITaskLimit(models.Model):
    """
    Per-AI workload limits configured by the client.
    Lets the client cap how many tasks/tokens Serea can consume in a period.
    """
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_limits')
    ai_employee = models.ForeignKey('workspace_admin.HiredAIEmployee', on_delete=models.CASCADE, related_name='limits')
    max_tasks_per_day = models.IntegerField(default=50, help_text="Max tasks Serea can process per day")
    max_tokens_per_month = models.IntegerField(default=0, help_text="0 = use tier default")
    is_paused = models.BooleanField(default=False, help_text="Temporarily pause this AI employee")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('client', 'ai_employee')

    def __str__(self):
        return f"Limits for {self.ai_employee.ai_name} ({self.client.email})"

class ConsoleModuleActivation(models.Model):
    """
    Tracks which base "OS Apps" the user has installed into their BengalBound Console.
    e.g., ai_workforce, bengalbound_hub
    """
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='active_modules')
    module_id = models.CharField(max_length=100, db_index=True)
    tier = models.CharField(max_length=50, default='free')
    is_active = models.BooleanField(default=True)
    activated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('client', 'module_id')

    def __str__(self):
        return f"{self.module_id} -> {self.client.email}"
