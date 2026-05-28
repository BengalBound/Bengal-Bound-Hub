from django.db import models
from core.models import BaseModel

class AgentCatalog(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    role = models.CharField(max_length=200)
    description = models.TextField()
    system_prompt = models.TextField()
    category = models.CharField(max_length=100)
    tier_required = models.CharField(max_length=20, default='entry')
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.role})"
