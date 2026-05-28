# Module Requirements: Kai — AI DevOps Engineer
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `kai` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)
> 🔗 GitHub API, GitLab API, Docker Hub, Kubernetes API, Prometheus, PagerDuty

---

## Section 1: Overview

**AI Employee Name:** Kai | **Department:** Engineering / DevOps
**Target Clients:** Software startups, SaaS companies, dev agencies, and any team running CI/CD pipelines without a dedicated DevOps engineer.
**Core Function:** Monitors CI/CD pipelines, auto-rolls back failed deployments, optimizes Docker images, generates infrastructure-as-code patches, and keeps the engineering team focused on features — not fires.
**Value Prop:** *"Your infrastructure never breaks in silence. Kai catches it, fixes it, and tells you about it."*

| | Human DevOps Engineer | Kai AI |
|---|---|---|
| Monthly Cost | ৳50,000–৳80,000 | ৳2,000 |
| Monitoring | Business hours | 24/7 |
| Incident Response | 15–60 min | Seconds |
| Pipeline Optimization | Ad-hoc | Continuous |

---

## Section 2: Core Capabilities

1. **Pipeline Monitor** — Connects to GitHub Actions/GitLab CI; monitors every build and deployment in real time
2. **Auto-Rollback** — On deploy failure, Kai immediately triggers rollback to the last stable version and notifies the team
3. **Failure Root Cause Analysis** — Gemini analyzes build logs and identifies the root cause (failing test, dependency conflict, env var missing)
4. **Docker Image Optimizer** — Scans Dockerfiles and suggests (or applies) size optimizations, layer caching improvements, security fixes
5. **IaC Patch Generator** — Generates Terraform/Kubernetes YAML patches for common infrastructure issues
6. **Uptime Monitor** — Pings all production endpoints every 60 seconds; alerts immediately on downtime
7. **Dependency Vulnerability Scanner** — Scans `package.json`, `requirements.txt`, `Gemfile` for known CVEs daily
8. **Weekly DevOps Report** — Summary of deployments, incidents, rollbacks, uptime %, and open vulnerabilities

---

## Section 3: Django Models

```python
class Pipeline(models.Model):
    PROVIDERS = [('github','GitHub Actions'),('gitlab','GitLab CI'),('circleci','CircleCI'),
                 ('jenkins','Jenkins')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='kai_pipelines')
    provider        = models.CharField(max_length=20, choices=PROVIDERS)
    repo_name       = models.CharField(max_length=300)
    repo_url        = models.URLField()
    api_token       = models.TextField()    # Encrypted
    webhook_secret  = models.CharField(max_length=200, blank=True)
    is_active       = models.BooleanField(default=True)

class Deployment(models.Model):
    STATUS = [('pending','Pending'),('running','Running'),('success','Success'),
              ('failed','Failed'),('rolled_back','Rolled Back')]
    pipeline        = models.ForeignKey(Pipeline, on_delete=models.CASCADE)
    commit_sha      = models.CharField(max_length=40)
    commit_message  = models.TextField()
    branch          = models.CharField(max_length=200)
    triggered_by    = models.CharField(max_length=200)
    status          = models.CharField(max_length=20, choices=STATUS)
    duration        = models.IntegerField(null=True)        # Seconds
    failure_reason  = models.TextField(blank=True)
    ai_root_cause   = models.TextField(blank=True)         # Gemini analysis
    auto_rolled_back = models.BooleanField(default=False)
    started_at      = models.DateTimeField()
    completed_at    = models.DateTimeField(null=True)

class UptimeCheck(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='kai_uptimechecks')
    name            = models.CharField(max_length=200)
    url             = models.URLField()
    check_interval  = models.IntegerField(default=60)       # Seconds
    is_up           = models.BooleanField(default=True)
    last_checked    = models.DateTimeField(null=True)
    last_downtime   = models.DateTimeField(null=True)
    uptime_pct_30d  = models.FloatField(null=True)

class Incident(models.Model):
    STATUS = [('open','Open'),('investigating','Investigating'),('resolved','Resolved')]
    uptime_check    = models.ForeignKey(UptimeCheck, on_delete=models.SET_NULL, null=True)
    deployment      = models.ForeignKey(Deployment, on_delete=models.SET_NULL, null=True)
    title           = models.CharField(max_length=500)
    description     = models.TextField()
    ai_summary      = models.TextField(blank=True)
    ai_fix          = models.TextField(blank=True)          # Gemini-suggested fix
    status          = models.CharField(max_length=20, choices=STATUS, default='open')
    duration_mins   = models.IntegerField(null=True)
    started_at      = models.DateTimeField(auto_now_add=True)
    resolved_at     = models.DateTimeField(null=True)

class DependencyVulnerability(models.Model):
    SEVERITY = [('critical','Critical'),('high','High'),('medium','Medium'),('low','Low')]
    pipeline        = models.ForeignKey(Pipeline, on_delete=models.CASCADE)
    package_name    = models.CharField(max_length=300)
    affected_version = models.CharField(max_length=100)
    fixed_version   = models.CharField(max_length=100, blank=True)
    cve_id          = models.CharField(max_length=50, blank=True)
    severity        = models.CharField(max_length=10, choices=SEVERITY)
    description     = models.TextField()
    fix_command     = models.TextField(blank=True)
    is_resolved     = models.BooleanField(default=False)
    found_at        = models.DateTimeField(auto_now_add=True)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/kai/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/pipelines/` | Connect repos/pipelines |
| `POST` | `/webhooks/github/` | GitHub Actions webhook |
| `POST` | `/webhooks/gitlab/` | GitLab CI webhook |
| `GET` | `/deployments/` | Deployment history |
| `GET` | `/deployments/failed/` | Failed deployments with root cause |
| `POST` | `/deployments/{id}/rollback/` | Manual rollback trigger |
| `GET/POST` | `/uptime/` | Manage uptime monitors |
| `GET` | `/uptime/status/` | Current status of all endpoints |
| `GET` | `/incidents/` | Incident log |
| `GET` | `/vulnerabilities/` | Dependency vulnerabilities |
| `GET` | `/reports/weekly/` | Weekly DevOps summary |
| `GET` | `/analytics/` | Deploy frequency, failure rate, MTTR, uptime |

---

## Section 5: Technical Stack

| Layer | Technology | Cost |
|---|---|---|
| AI Engine | LiteLLM proxy → Gemini 1.5 Flash | ✅ FREE |
| GitHub | GitHub REST API + Webhooks | ✅ FREE |
| GitLab | GitLab API + Webhooks | ✅ FREE |
| Uptime Monitoring | Custom `requests` pinger | ✅ FREE |
| Docker Analysis | Docker API via `docker-py` | ✅ FREE |
| Notifications | Slack Webhooks + Gmail SMTP | ✅ FREE |
| Task Queue | `django-apscheduler` | ✅ FREE |
| Vuln Scanning | `pip-audit`, `npm audit`, `safety` | ✅ FREE |

```
pip install requests docker pip-audit safety django-apscheduler PyGithub
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

---

## Section 6: Phased Delivery

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | GitHub webhook, deployment log, failure detection + root cause, uptime pinger, Slack alerts | Weeks 1–6 |
| Phase 2 | Auto-rollback, GitLab support, dependency scanner, incident log, weekly report | Weeks 7–12 |
| Phase 3 | Docker optimizer, IaC patch generator, Kubernetes health checks, MTTR analytics | Weeks 13–20 |

---

## Section 7: Pricing Tiers

| Tier | Monthly | Repos | Features |
|---|---|---|---|
| Intern | Free | 1 | Pipeline log, failure alerts |
| Entry | ৳2,000 | 3 | Auto-rollback, uptime monitoring |
| Mid | ৳5,000 | 10 | Dep scanner, incident log, weekly report |
| Senior | ৳10,000 | Unlimited | Docker optimizer, IaC patches, analytics |

---
*BengalBound HUB — dev branch*
