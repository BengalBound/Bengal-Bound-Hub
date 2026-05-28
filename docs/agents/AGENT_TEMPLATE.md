# BengalBound Agent — Python Template

This document shows the exact file-by-file pattern every agent app must follow in the BengalBound HUB project. Use it as a copy-paste starting point when implementing any of the 30 agents.

Replace `<name>` with the agent slug (e.g. `aria`), `<Name>` with the class name (e.g. `Aria`), and `<NAME>` with the constant prefix (e.g. `ARIA`).

---

## Directory structure

```
agents/
  <name>/
    __init__.py
    apps.py
    models.py
    serializers.py
    views.py
    urls.py
    admin.py
    migrations/
      __init__.py
```

---

## `apps.py`

```python
from django.apps import AppConfig


class <Name>Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.<name>"
    verbose_name = "<Name> Agent"
```

---

## `models.py`

Domain models specific to this agent. All FKs point to `'bredbound.BusinessInstance'`.

```python
from django.db import models
from django.conf import settings


class <Name>Task(models.Model):
    """Primary work unit for the <Name> agent."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    business = models.ForeignKey(
        "bredbound.BusinessInstance",
        on_delete=models.CASCADE,
        related_name="<name>_tasks",
    )
    # Add domain-specific fields here, e.g.:
    # title = models.CharField(max_length=255)
    # description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    ai_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="<name>_tasks",
    )

    class Meta:
        app_label = "agents_<name>"
        ordering = ["-created_at"]

    def __str__(self):
        return f"<Name>Task #{self.pk} [{self.status}]"
```

---

## `serializers.py`

```python
from rest_framework import serializers
from .models import <Name>Task


class <Name>TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = <Name>Task
        fields = "__all__"
        read_only_fields = ("ai_response", "created_at", "updated_at")
```

---

## `views.py`

All agent views use `agent_chat()` from `agents.utils` — never call any AI provider directly.

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from hub.models import BusinessInstance, BusinessEmployee
from agents.utils import agent_chat
from .models import <Name>Task
from .serializers import <Name>TaskSerializer

_<NAME>_SYSTEM_PROMPT = """
You are <Name>, a specialist AI assistant for BengalBound HUB.

[DESCRIBE THE AGENT'S ROLE, PERSONALITY, AND RESPONSIBILITIES HERE]

Always be professional, accurate, and business-focused.
"""

_<NAME>_MODEL = "neural-chat"   # Override with 'gemini/gemini-1.5-flash' for complex tasks


class <Name>TaskViewSet(viewsets.ModelViewSet):
    serializer_class = <Name>TaskSerializer

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        return <Name>Task.objects.filter(business=business)

    def perform_create(self, serializer):
        slug = self.kwargs.get("slug")
        business = get_object_or_404(BusinessInstance, slug=slug)
        serializer.save(business=business, created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="process")
    def process(self, request, slug=None, pk=None):
        """Run the <Name> agent on this task."""
        task = self.get_object()

        messages = [
            {"role": "system", "content": _<NAME>_SYSTEM_PROMPT},
            {"role": "user", "content": str(task)},  # Customise this
        ]

        try:
            response = agent_chat(messages, model=_<NAME>_MODEL)
            task.ai_response = response
            task.status = "completed"
            task.save(update_fields=["ai_response", "status", "updated_at"])
            return Response({"response": response, "status": "completed"})
        except Exception as exc:
            task.status = "failed"
            task.save(update_fields=["status", "updated_at"])
            return Response(
                {"error": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
```

---

## `urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import <Name>TaskViewSet

app_name = "<name>"

router = DefaultRouter()
router.register(r"tasks", <Name>TaskViewSet, basename="<name>-task")

urlpatterns = [
    path("", include(router.urls)),
]
```

---

## `admin.py`

```python
from django.contrib import admin
from .models import <Name>Task


@admin.register(<Name>Task)
class <Name>TaskAdmin(admin.ModelAdmin):
    list_display = ("pk", "business", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("business__name",)
    readonly_fields = ("ai_response", "created_at", "updated_at")
```

---

## `migrations/__init__.py`

```python
```

---

## `agents/utils.py` (shared — create once)

```python
import json
import requests
from django.conf import settings
from .toolkit import UNIVERSAL_TOOLS, execute_tool

def agent_chat(messages: list, model: str = None) -> str:
    """
    Send messages to the LiteLLM proxy and return the assistant reply.
    Now equipped with the Universal Toolkit loop for autonomous internet/API access.
    """
    model = model or settings.SEREA_TASK_MODELS.get("chat", "neural-chat")
    
    # Inject tool awareness into the system prompt automatically
    messages_copy = list(messages)
    for m in messages_copy:
        if m.get("role") == "system":
            instruction = "\n\n[SYSTEM]: You are an autonomous AI. You have access to tools that can search the internet, scrape websites, and call APIs. Use them whenever you need real-time information or external data."
            if instruction not in m.get("content", ""):
                m["content"] += instruction
            break
            
    for _ in range(5):  # Max 5 tool iterations
        resp = requests.post(
            f"{settings.LITELLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"},
            json={"model": model, "messages": messages_copy, "tools": UNIVERSAL_TOOLS},
            timeout=45,
        )
        resp.raise_for_status()
        
        message = resp.json()["choices"][0]["message"]
        
        if message.get("tool_calls"):
            messages_copy.append(message)
            for tc in message["tool_calls"]:
                tool_name = tc["function"]["name"]
                try:
                    arguments = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    arguments = {}
                    
                result = execute_tool(tool_name, arguments)
                messages_copy.append({
                    "role": "tool",
                    "name": tool_name,
                    "tool_call_id": tc["id"],
                    "content": str(result)
                })
        else:
            return message.get("content", "")
            
    return "Error: Exceeded maximum tool call iterations."
```

---

## Register the app

In `bengalbound_core/settings/base.py`, add to `INSTALLED_APPS`:
```python
"agents.<name>",
```

---

## Mount the URL

In `bengalbound_core/urls.py`, inside the `hub/<slug>/` block:
```python
path("hub/<slug:slug>/agents/<name>/", include("agents.<name>.urls")),
```

---

## Seed entry

In `agents/management/commands/seed_agents.py`, add to `AGENTS`:
```python
{
    "name": "<Name>",
    "slug": "<name>",
    "role": "<One-line role description>",
    "description": "<2-3 sentence description>",
    "system_prompt": _<NAME>_SYSTEM_PROMPT,   # import from views
    "category": "<Category>",
    "tier_required": "entry",
    "icon": "",
},
```

---

## Key constraints (repeat for every agent)

1. FK to tenant: `"bredbound.BusinessInstance"` — never `"hub.BusinessInstance"`
2. AI calls: `agent_chat()` from `agents.utils` — never direct Groq/OpenAI/Gemini
3. View signature: all views accept `slug` kwarg and verify business + employee access
4. App label: set in `apps.py` as `"agents.<name>"` (hyphenated slugs become underscored: `lead_hunter`)
