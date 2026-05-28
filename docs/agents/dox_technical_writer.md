# Module Requirements: Dox — AI Technical Writer
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `dox` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)

---

## Section 1: Overview

**AI Employee Name:** Dox | **Department:** Documentation & Knowledge
**Core Function:** Generates and maintains technical documentation, API docs, user manuals, SOPs, and internal wikis — turning codebases, features, and workflows into clear, structured documentation automatically.
**Value Prop:** *"Docs written, updated, and maintained automatically. Your team always has the answers."*

---

## Section 2: Core Capabilities

1. **API Documentation Generator** — Reads OpenAPI/Swagger specs or Django URL conf and generates full API reference docs
2. **User Manual Creator** — Gemini writes step-by-step user guides from feature descriptions or product screenshots
3. **SOP Generator** — Converts workflow descriptions into formatted Standard Operating Procedures
4. **Code Comment Writer** — Analyses Python/JS/etc functions and writes clear docstrings and inline comments
5. **Wiki Builder** — Maintains a searchable internal knowledge wiki; auto-updates when code or processes change
6. **Changelog Generator** — Reads git commits and generates human-readable release notes / changelogs
7. **Doc Health Monitor** — Identifies outdated documentation (references deprecated code/features) and flags for update
8. **Video Script Writer** — Gemini converts feature docs into narrated tutorial video scripts

---

## Section 3: Django Models

```python
class DocumentationProject(models.Model):
    TYPES = [('api','API Reference'),('user_manual','User Manual'),('sop','SOP'),
             ('wiki','Internal Wiki'),('changelog','Changelog'),('code_docs','Code Documentation')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='dox_documentationprojects')
    name            = models.CharField(max_length=300)
    doc_type        = models.CharField(max_length=20, choices=TYPES)
    repo_url        = models.URLField(blank=True)
    base_url        = models.URLField(blank=True)      # Product URL for crawling
    description     = models.TextField(blank=True)
    is_active       = models.BooleanField(default=True)
    last_generated  = models.DateTimeField(null=True)

class DocPage(models.Model):
    STATUS = [('draft','Draft'),('published','Published'),('outdated','Outdated'),('archived','Archived')]
    project         = models.ForeignKey(DocumentationProject, on_delete=models.CASCADE)
    title           = models.CharField(max_length=500)
    slug            = models.SlugField(max_length=300)
    content         = models.TextField()               # Markdown content
    section         = models.CharField(max_length=200, blank=True)
    version         = models.CharField(max_length=50, blank=True)
    status          = models.CharField(max_length=20, choices=STATUS, default='draft')
    ai_generated    = models.BooleanField(default=True)
    word_count      = models.IntegerField(default=0)
    last_reviewed   = models.DateTimeField(null=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

class Changelog(models.Model):
    project         = models.ForeignKey(DocumentationProject, on_delete=models.CASCADE)
    version         = models.CharField(max_length=50)
    release_date    = models.DateField()
    summary         = models.TextField()
    new_features    = models.JSONField(default=list)
    bug_fixes       = models.JSONField(default=list)
    breaking_changes = models.JSONField(default=list)
    raw_commits     = models.TextField(blank=True)
    generated_at    = models.DateTimeField(auto_now_add=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/dox/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/projects/` | Manage doc projects |
| `POST` | `/projects/{id}/generate/` | AI-generate documentation |
| `GET` | `/pages/` | Browse doc pages |
| `GET` | `/pages/{id}/` | Page content |
| `PATCH` | `/pages/{id}/` | Update doc page |
| `GET` | `/pages/outdated/` | Pages flagged as outdated |
| `POST` | `/changelog/generate/` | Generate changelog from git commits |
| `GET` | `/search/` | Full-text search across all docs |
| `GET` | `/analytics/` | Page views, search queries, outdated count |

---

## Section 5: Tech Stack & Delivery

```
pip install PyGithub python-markdown mistune django-apscheduler
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Manual doc generation (text input), SOP + user manual, Markdown output | Weeks 1–4 |
| Phase 2 | API doc from OpenAPI spec, changelog from git, doc search | Weeks 5–9 |
| Phase 3 | Code comment writer, outdated doc detection, video script, wiki builder | Weeks 10–14 |

| Tier | Monthly | Pages | Features |
|---|---|---|---|
| Intern | Free | 10 | Manual generation |
| Entry | ৳2,000 | 50 | API docs, SOP, changelog |
| Mid | ৳5,000 | 200 | Code comments, wiki, search |
| Senior | ৳10,000 | Unlimited | All types + doc health monitor |

*BengalBound HUB — dev branch*
