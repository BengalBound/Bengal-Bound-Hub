# BengalBound HUB — Technical Standards & Guidelines
# BengalBound Ltd | "Light. Easy. Powerful."

> **Document Class:** Coding Standards & Engineering Guide  
> **Target Audience:** All Software Engineers & AI Pair Programming Assistants  
> **Date:** May 2026 | **Version:** 1.0  

---

## 1. Django App Architecture

Every pluggable business module and AI agent added to the BengalBound HUB MUST strictly follow these standard formatting practices to prevent system regressions:

### App Structure
```
 agents/
   <agent_slug>/
     __init__.py
     apps.py           ← Name must equal 'agents.<agent_slug>'
     models.py         ← All ForeignKeys target 'bredbound.BusinessInstance'
     views.py          ← Accepts request and URL kwargs; verifies business access
     serializers.py    ← DRF serializers inheriting from serializers.ModelSerializer
     urls.py           ← Maps router patterns cleanly
     admin.py          ← Registers models in standard grid views
```

### Critical Rules
1.  **Never Change the App Label:** The core tenant app folder is named `hub/`, but the database label is strictly `bredbound`. Changing this breaks all database relations.
2.  **LiteLLM Interceptor:** Direct API requests to OpenAI, Anthropic, or Google are strictly forbidden. All operations MUST use `agents.utils.agent_chat()`.

---

## 2. Code Quality & Formatting

*   **Python Formatting:** Follow PEP 8 guidelines. Keep code structures clean and maintain documentation integrity.
*   **Aesthetics Priority:** Use curating, modern UI components tailored to Outfit and Inter fonts. Avoid default visual primitives.
