# BengalBound HUB — QA & Testing Playbook
# BengalBound Ltd | "Light. Easy. Powerful."

> **Document Class:** Technical QA Standard  
> **Target Audience:** Core Developers, QA Engineers, DevOps Teams  
> **Date:** May 2026 | **Version:** 1.0  

---

## 1. Quality Assurance Strategy

To maintain high structural integrity across a 60+ module codebase, we enforce a strict multi-tier testing framework.

```
       [ Automated CI/CD Pipeline ]
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
 [ Unit Tests ] [ DRF API Tests ] [ Browser Tests ]
  - Models       - Serializers    - End-to-End
  - Logic        - ViewSets       - UI Flows
```

---

## 2. Test Suites Guidelines

### Code Coverage Targets
*   **Core Systems (`hub/`, `accounts/`):** 80%+ coverage required before production deployments.
*   **AI Engine (`serea/`, `agents/`):** 75%+ coverage target, utilizing robust API mock layers for LiteLLM requests.

### Execution Commands

```bash
# Run all unit and integration tests
python manage.py test

# Run tests with coverage tracking
coverage run --source=hub,accounts,serea manage.py test
coverage report -m
```
