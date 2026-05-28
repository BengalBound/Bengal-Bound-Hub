# Developer Kit — BengalBound Platform
# BengalBound Ltd | v1.0

---

## 1. Day 1 Setup

### Install in Order:
```
1. Git 2.45+        → git-scm.com
2. Python 3.12      → python.org
3. Node.js 20 LTS   → nodejs.org (use nvm)
4. VS Code          → code.visualstudio.com
```

### VS Code Extensions (Required):
`Python` · `Pylance` · `Ruff` · `Black Formatter` · `Prettier` · `GitLens` · `Tailwind CSS IntelliSense`

### Clone & Run:
```bash
# Clone the repository
git clone https://github.com/Adre-melech/BengalBound.git
cd BengalBound/dev-backoffice

# API Setup
python -m venv .venv
.venv\Scripts\activate # Windows
# source .venv/bin/activate # macOS/Linux

pip install -r requirements.txt
cp .env.example .env

# Set environment
export DJANGO_SETTINGS_MODULE=bengalbound_core.settings.development

# Run migrations & seed catalog
python manage.py migrate
python manage.py seed_modules
python manage.py seed_agents

# Run server on port 1234
python manage.py runserver 0.0.0.0:1234
```

---

## 2. Git Workflow

### Branch Naming Conventions:
```
feature/BENGAL-123-aria-support-viewsets
fix/BENGAL-456-inspector-pii-redaction
hotfix/BENGAL-999-auth-session-hijack
```

### Commit Formats (Conventional Commits):
```
feat: add Zendesk webhook endpoint to Aria Support
fix: BusinessAccessMiddleware skipping suite-first ERP prefix
test: add unit tests for Serea content scheduling
```

---

## 3. Coding Standards

### Python Typing Hints & Managers:
```python
# ✅ Enforce type hinting
def moderate_comment(comment_text: str, agent_id: int) -> dict:
    ...

# ✅ Filter queries by current business (multi-tenancy)
contacts = Contact.objects.filter(business=request.current_business)
```

---

## 4. Environment Configurations

### Dev Defaults (.env):
```bash
DEBUG=True
SECRET_KEY=bengalbound-local-key
LITELLM_BASE_URL=https://ai.neurolinkit.com/v1
LITELLM_MASTER_KEY=local-dev-key
```

### Production Setup (Hetzner VPS):
*   `DEBUG=False`
*   `CELERY_BROKER_URL` set to Redis backend broker.
*   Production Gunicorn binding behind Nginx gateway.
