# BengalBound Agent — Full Mini-Platform Template

Every agent in BengalBound HUB is a **self-contained mini-platform**, not just a task runner. This template shows the exact file structure and code patterns required.

Replace `<name>` (lowercase, underscored) · `<Name>` (PascalCase) · `<slug>` (hyphenated, matches AgentCatalog slug).

---

## Directory Structure

```
agents/<name>/
  __init__.py
  apps.py           ← AppConfig with ready() to wire signals
  engine.py         ← AI brain: SYSTEM_PROMPT + domain methods + PermissionRequired
  tasks.py          ← Autonomous Celery tasks on their own schedule
  signals.py        ← Auto-provisions AgentInstance when business hires this agent
  admin.py          ← Django admin for domain models + AgentLog inline
  webhooks.py       ← Inbound webhook handler (external → agent event routing)
  models.py         ← Domain models (FK → 'bredbound.BusinessInstance')
  serializers.py    ← DRF serializers
  views.py          ← DRF ViewSets
  urls.py           ← app_name = '<name>'
  migrations/
    __init__.py
    0001_initial.py
```

---

## `apps.py`

```python
from django.apps import AppConfig


class <Name>Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.<name>"
    verbose_name = "<Name> — <Role>"

    def ready(self):
        import agents.<name>.signals  # noqa
```

---

## `engine.py`

The AI brain. Always includes `PermissionRequired` for human-in-the-loop flow. Every method accepts an optional `instance` param and logs to `AgentLog`.

```python
import json
from django.conf import settings
from agents.utils import agent_chat


class PermissionRequired(Exception):
    """Raised when agent confidence is below threshold — requires human approval."""
    def __init__(self, context: str, option_a: str, option_b: str = ''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b


SYSTEM_PROMPT = """You are <Name>, BengalBound's <Role>.

[Describe capabilities, domain knowledge, and working principles here.]

Tone: [professional/warm/analytical/etc.]"""


class <Name>Engine:
    SYSTEM_PROMPT = SYSTEM_PROMPT
    CONFIDENCE_THRESHOLD = 0.8  # Below this → raises PermissionRequired

    def primary_action(self, domain_object, instance=None) -> dict:
        prompt = f"""[Task-specific prompt using domain_object fields.]

Return JSON: {{
  "result": "...",
  "confidence": 0.0-1.0,
  "needs_human": boolean
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = {"result": raw, "confidence": 0.5, "needs_human": True}

        # Log to AgentLog before raising
        if instance:
            from agents.models import AgentLog
            AgentLog.objects.create(
                instance=instance,
                action=f"primary_action #{domain_object.pk}",
                outcome='pending' if result.get('needs_human') else 'success',
                detail=json.dumps(result),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'neural-chat'),
            )

        if result.get('confidence', 1.0) < self.CONFIDENCE_THRESHOLD:
            raise PermissionRequired(
                context=f"Unsure about action on #{domain_object.pk}: confidence {result['confidence']}",
                option_a="Approve the suggested action.",
                option_b="Deny and assign to a human.",
            )

        return result
```

---

## `tasks.py`

Always loads `AgentInstance` per-business at task start. Catches `PermissionRequired` and sends email notification. Never hard-codes business IDs.

```python
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.<name>.primary_batch_task")
def primary_batch_task():
    from agents.<name>.models import DomainModel
    from agents.<name>.engine import <Name>Engine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest
    from agents.platform.email_notify import EmailAdapter

    catalog = AgentCatalog.objects.filter(slug='<slug>').first()
    if not catalog:
        return 0

    engine = <Name>Engine()
    processed = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        items = DomainModel.objects.filter(business=instance.business, status='pending')
        for item in items:
            try:
                result = engine.primary_action(item, instance=instance)
                # Apply result to domain model
                processed += 1
            except PermissionRequired as pr:
                req = AgentPermissionRequest.objects.create(
                    instance=instance,
                    context=pr.context,
                    option_a=pr.option_a,
                    option_b=pr.option_b,
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])

                # Notify business owner
                emails = _get_owner_emails(instance)
                EmailAdapter(instance).send_permission_request(req, emails)
            except Exception as exc:
                logger.error("agents.<name>.primary_batch_task item %s: %s", item.pk, exc)

    logger.info("agents.<name>.primary_batch_task: processed %d items", processed)
    return processed


def _get_owner_emails(instance) -> list:
    try:
        if hasattr(instance.business, 'owner') and instance.business.owner.email:
            return [instance.business.owner.email]
        if hasattr(instance.business, 'users'):
            return [u.email for u in instance.business.users.all() if u.email]
    except Exception:
        pass
    return ['admin@bengalbound.com']
```

---

## `signals.py`

Auto-provisions an `AgentInstance` when a business hires this agent via `HiredAIEmployee`.

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from workspace_admin.models import HiredAIEmployee
from agents.models import AgentInstance


@receiver(post_save, sender=HiredAIEmployee)
def provision_<name>_instance(sender, instance, created, **kwargs):
    if not getattr(instance, 'agent_catalog', None) or instance.agent_catalog.slug != '<slug>':
        return
    if instance.is_active:
        business = instance.employer.owned_businesses.first()
        if not business:
            return
        obj, is_new = AgentInstance.objects.get_or_create(
            business=business,
            catalog=instance.agent_catalog,
            defaults={'hired_employee': instance, 'status': 'idle'},
        )
        if not is_new and obj.status == 'offline':
            obj.status = 'idle'
            obj.save(update_fields=['status'])
    else:
        AgentInstance.objects.filter(hired_employee=instance).update(status='offline')
```

---

## `admin.py`

```python
from django.contrib import admin
from agents.<name>.models import DomainModel


@admin.register(DomainModel)
class DomainModelAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'business', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['business__name']
```

---

## `webhooks.py`

Called by the universal inbound webhook receiver at `POST /agents/webhook/<token>/`.

```python
def handle_event(event_type: str, payload: dict, instance):
    """Route inbound webhook payload to the agent's engine."""
    from agents.<name>.models import DomainModel
    from agents.<name>.engine import <Name>Engine

    engine = <Name>Engine()
    if event_type == 'webhook_event':
        # Create domain model from payload, run engine
        obj = DomainModel.objects.create(
            business=instance.business,
            # map payload fields here
        )
        try:
            engine.primary_action(obj, instance=instance)
        except Exception:
            pass


def handle_permission_resume(perm_request, instance):
    """
    Optional hook — called by resume_after_permission task after human approves/denies.
    Implement this to execute the approved action rather than waiting for next beat cycle.
    """
    if perm_request.decision != 'approved':
        return
    # Re-run the action that was pending
```

---

## `models.py`

```python
import uuid
from django.db import models
from core.models import BaseModel  # provides created_at, updated_at


class DomainModel(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(
        'bredbound.BusinessInstance',   # NEVER 'hub.BusinessInstance'
        on_delete=models.CASCADE,
        related_name='<name>_items',
    )
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('processing', 'Processing'),
                 ('completed', 'Completed'), ('failed', 'Failed')],
        default='pending',
    )
    ai_output = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"<Name> #{self.pk} [{self.status}]"
```

---

## `serializers.py`

```python
from rest_framework import serializers
from .models import DomainModel


class DomainModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DomainModel
        fields = '__all__'
        read_only_fields = ['id', 'ai_output', 'created_at', 'updated_at']
```

---

## `views.py`

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from hub.models import BusinessInstance, BusinessEmployee
from .models import DomainModel
from .serializers import DomainModelSerializer


class DomainModelViewSet(viewsets.ModelViewSet):
    serializer_class = DomainModelSerializer
    permission_classes = [IsAuthenticated]

    def _get_business(self):
        return get_object_or_404(BusinessInstance, slug=self.kwargs['slug'])

    def get_queryset(self):
        business = self._get_business()
        get_object_or_404(BusinessEmployee, business=business, user=self.request.user)
        return DomainModel.objects.filter(business=business)

    def perform_create(self, serializer):
        serializer.save(business=self._get_business())

    @action(detail=True, methods=['post'])
    def process(self, request, slug=None, pk=None):
        obj = self.get_object()
        from agents.<name>.tasks import primary_batch_task
        primary_batch_task.delay()  # or pass obj.pk if task is per-item
        return Response({'status': 'queued'})
```

---

## `urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DomainModelViewSet

app_name = '<name>'

router = DefaultRouter()
router.register(r'items', DomainModelViewSet, basename='items')

urlpatterns = [path('', include(router.urls))]
```

---

## Register the Agent

**1. `bengalbound_core/settings/base.py`** — add to `INSTALLED_APPS`:
```python
'agents.<name>',
```

**2. `bengalbound_core/settings/base.py`** — add to `CELERY_BEAT_SCHEDULE`:
```python
'<name>-primary-task': {'task': 'agents.<name>.primary_batch_task', 'schedule': 86400},
```

**3. `bengalbound_core/urls.py`** — mount URL:
```python
path('hub/<slug:slug>/agents/<slug>/', include('agents.<name>.urls', namespace='<name>')),
```

**4. `agents/management/commands/seed_agents.py`** — add to `AGENTS` list:
```python
{
    "name": "<Name>",
    "slug": "<slug>",
    "role": "<One-line role>",
    "description": "<2-3 sentence description>",
    "system_prompt": "",   # populated from engine.SYSTEM_PROMPT at runtime
    "category": "<Category>",
    "tier_required": "entry",
    "icon": "",
},
```

**5. Create and apply migration:**
```bash
python manage.py makemigrations <name>
python manage.py migrate
python manage.py seed_agents
```

---

## Deploying an Agent Externally

Any agent can be used by external systems without being inside a BengalBound module.

### Option 1 — REST API
```bash
# Get agent output via REST
POST /hub/<business-slug>/agents/<agent-slug>/items/
Authorization: Token <your-token>
Content-Type: application/json
{"field": "value"}
```

### Option 2 — Inbound Webhook
```python
# Register a webhook endpoint
AgentWebhookEndpoint.objects.create(
    instance=agent_instance,
    source='your-system',
    url_token='<unique-256bit-token>',
    secret='<hmac-key>',
)

# External system posts to:
# POST /agents/webhook/<token>/
# X-Hub-Signature-256: sha256=<hmac>
```

### Option 3 — Standalone Celery Task
Set `AgentInstance.status = 'idle'` and the agent's Celery Beat tasks fire automatically on schedule, reading from whatever `AgentIntegration` credentials are stored.

---

## Critical Rules

| Rule | Detail |
|------|--------|
| FK to tenant | Always `'bredbound.BusinessInstance'` — never `'hub.BusinessInstance'` |
| AI calls | Always `agent_chat()` from `agents.utils` — never direct OpenAI/Groq/Gemini |
| View pattern | All views accept `slug` kwarg, verify business + employee access |
| App name | `apps.py` name = `"agents.<name>"` (hyphens become underscores) |
| Migrations | Create with `makemigrations <name>`, not `makemigrations agents` |
| Permission flow | Raise `PermissionRequired` for confidence < threshold, never silently act |
