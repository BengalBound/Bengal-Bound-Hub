# Test Plan — BengalBound HUB
# BengalBound Ltd | ISO 29119 Aligned | v1.0

---

## 1. Scope
This test plan defines the testing strategies, targets, and criteria for the BengalBound HUB:
*   Django REST API Backend
*   Hiring Console & Admin Portal
*   Inspector compliance middleware watchdog
*   Serea scheduled AI queues

---

## 2. Test Types

### 2.1 Unit Tests (pytest + pytest-django)
*   **Target Coverage:** 80% overall | 95% for security-critical (Inspector, Auth) modules.
*   **Current state:** 219 tests passing, 0 failures (June 2026).
*   **Runner:** `python -m pytest` (not `manage.py test`).
*   **Rules:** Mock external LiteLLM API responses dynamically to prevent slow tests. Use `@patch('serea.tasks.<fn>.delay')` not `serea.views.<fn>.delay` for Celery task mocks.

```bash
# Run full suite
python -m pytest

# With coverage
python -m pytest --cov --cov-report=term-missing

# Single test file
python -m pytest tests/test_accounts.py -v

# Keyword filter
python -m pytest -k "aria or crux"
```

```python
# Example: Inspector Fail-Closed Test
def test_inspector_fails_closed_when_ai_down(self):
    with mock.patch("inspector.services.completion") as mock_comp:
        mock_comp.side_effect = Exception("LiteLLM connection timeout")
        result = Inspector.evaluate(action, client_id="test-client")
        self.assertEqual(result.decision, "BLOCKED")
        self.assertEqual(result.reason, "Inspector unavailable - fail closed")
```

### 2.2 E2E Integration (Playwright)
*   Verify user registration → email authentication → organization creation → agent hiring → agent active state transition.
*   Validate the **HITL (Human-In-The-Loop)** flow: Agent requests approval → Alert appears in Console → User approves → Action resumes.

### 2.3 Performance & Security Audits
*   **Performance:** Verify p95 API response times `< 800ms`, and Inspector gate evaluation `< 500ms` under 50 concurrent sessions using Locust.
*   **Security:** Daily automated container vulnerability scans (`Trivy`) and Bandit SAST checks on pull requests.

---

## 3. Bug Severity & SLA Response

| Severity | Definition | SLA Response |
|---|---|---|
| **Critical** | Security exploit, data leak, Inspector bypass, server down | Fix within 4 hours |
| **High** | Core feature broken, payments failing, background tasks stalled | Fix within 24 hours |
| **Medium** | Chart broken, UI misalignment, non-blocking glitches | Fix within 72 hours |
| **Low** | Typos, minor cosmetics | Next sprint |
