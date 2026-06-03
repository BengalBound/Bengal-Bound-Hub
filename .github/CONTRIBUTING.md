# Contributing to BengalBound HUB

Thank you for contributing. Please read this before opening a PR.

---

## Branch Strategy

- `main` — production-ready, protected. Never push directly.
- `dev` — integration branch. All PRs target `dev`.
- Feature branches: `feat/<name>`, bugfix branches: `fix/<name>`

## Development Setup

```bash
git clone -b dev https://github.com/Adre-melech/BengalBound.git
cd BengalBound
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # fill in SECRET_KEY at minimum
python manage.py migrate
python manage.py seed_modules
python manage.py seed_agents
python manage.py runserver 0.0.0.0:1234
```

> Port **1234** is required — CSRF_TRUSTED_ORIGINS is configured for it.

## Critical Rules

Read `CLAUDE.md` fully before editing. The hard rules:

1. **App label:** Hub folder = `bredbound`. All FKs use `'bredbound.BusinessInstance'` — never `'hub.BusinessInstance'`.
2. **AI calls:** Always through `agents/utils.py:agent_chat()` → LiteLLM proxy. Never call Groq, OpenAI, or Gemini directly.
3. **New agent apps:** Follow the pattern in `docs/agents/AGENT_TEMPLATE.md`.
4. **New suite-first URLs:** Add the prefix to `_SKIP_SEGMENTS` in `hub/middleware.py`.
5. **Settings:** Secrets go in `.env` only — never in `base.py`, `development.py`, or `production.py`.

## Running Tests

```bash
python -m pytest                          # full suite
python -m pytest tests/test_accounts.py  # single file
python -m pytest -k "test_aria"          # keyword filter
python -m pytest --cov --cov-report=term-missing  # with coverage
```

All PRs must pass the full suite before merging.

## Adding a New Agent

1. Create `agents/<name>/` following the structure in `docs/agents/AGENT_TEMPLATE.md`
2. Register in `INSTALLED_APPS` in `bengalbound_core/settings/base.py`
3. Add URL include in `bengalbound_core/urls.py`
4. Add entry to `agents/management/commands/seed_agents.py`
5. Add `queryset = Model.objects.none()` to every ViewSet class
6. Run `python manage.py makemigrations <name> && python manage.py migrate`
7. Run `python manage.py seed_agents` to seed the catalog
8. Write a `README.md` in the agent folder

## PR Checklist

- [ ] `python -m pytest` passes (0 failures)
- [ ] `python manage.py check` reports 0 issues
- [ ] No secrets committed (`.env` is gitignored)
- [ ] No direct AI provider calls (use `agent_chat()` only)
- [ ] FKs use `'bredbound.BusinessInstance'`
- [ ] New agent has `README.md` and `queryset = Model.objects.none()` on all ViewSets

## Commit Style

```
feat: add X
fix: correct Y
refactor: restructure Z
docs: update CEO action plan
test: add tests for aria suggest-response
```

Keep commit messages under 72 characters on the first line.
