# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Twilio Voice Receptionist integration:** `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` wired into settings; `twilio>=9.0.0` added to `requirements.txt`; `setup_voice_receptionist` management command created; full admin panel with webhook URL display
- **Voice Receptionist BusinessProfile:** Created for `bengalbound` slug linked to Twilio `+18664030430` with Aria as AI receptionist name
- **Stripe dependency:** Added `stripe>=8.0.0` to `requirements.txt` (was causing Cloud Run startup crash: `ModuleNotFoundError: No module named 'stripe'`)
- **Google Cloud Run deployment:** `bengal-bound-hub` service deployed in `us-south1`, project `serea-ai-agent-489222`; service URL: `https://bengal-bound-hub-u5i67kezxa-vp.a.run.app`
- **Swagger / OpenAPI docs:** Live at `/api/docs/` (Swagger UI) and `/api/redoc/` (ReDoc) via `drf-spectacular`
- **GitHub CONTRIBUTING.md and PR template:** `.github/CONTRIBUTING.md` and `.github/PULL_REQUEST_TEMPLATE.md` created
- **Agent READMEs:** Created missing `README.md` for aria, crux, mira, lead_hunter, content_strategist, scribe, pitch_presenter, video_concierge
- **CEO action plan updated:** Marked Sprint A/B done, Cloud Run live, Twilio done; added immediate next actions and key links table
- **Testing Environment**: Added `bengalbound_core/settings/testing.py` to enforce strict environment separation (ISO/IEC 27001).
- **Verification Scripts**: Added `verify.sh` and `verify.bat` for automated testing and linting (NIST SP 800-218).
- **SBOM**: Generated `sbom.json` using CycloneDX to track all Python dependencies (EO 14028).

### Changed
- **All 32 agent ViewSets:** Added `queryset = Model.objects.none()` to every ViewSet class — clears all 93 `drf_spectacular.W001` warnings; `python manage.py check` now reports 0 issues
- **Test suite migrated to pytest:** Test commands updated in README and TEST_PLAN.md (`python -m pytest` instead of `python manage.py test`); 219 tests passing
- **`requirements.txt` cleaned:** Removed full duplicate block (was 87 lines with lines 1–34 duplicated); now clean 57-line file
- **`accounts/views.py`:** Social provider URL building moved to view layer with per-provider exception handling; removes `SocialApp.DoesNotExist` crash in test environments
- **`templates/accounts/register.html`:** Removed `{% load socialaccount %}` template tag dependency; social login buttons now driven by context variable
- **Agent Mini-Platform**: Migrated all 30 agents to the new live `AgentInstance` architecture, upgrading them from standalone celery task runners to a robust platform tier system.
- **Repository Root Structure**: Consolidated scratch files (`test.py`, `scaffold_agents.py`, etc.) into a dedicated `scripts/` directory to declutter the root.

### Fixed
- `test_register_duplicate_email_fails` — `SocialApp.DoesNotExist` crash when no OAuth apps in test DB
- `test_litellm_chatopenai_selected_with_correct_settings` — ChatOpenAI called 0 times due to localhost bypass in `_get_llm()`
- `test_process_comment_records_tokens` — structured output path made live LLM call in test
- `test_process_comment_handles_exception` — structured output succeeded before `_run` mock reached
- `test_totp_challenge_intercepts_login` — `DisallowedHost: console.localhost:1234` — fixed with `self.settings(ALLOWED_HOSTS=[...])`
- `test_permission_respond_approve` — wrong patch target (`serea.views` vs `serea.tasks`) and form vs JSON body mismatch
- `test_agent_logs` — expected key `action_taken` but view serialises as `action`
- Cloud Run startup crash: `ModuleNotFoundError: No module named 'stripe'`

### Security
- **Data Protection**: Explicitly added certificates (`*.pem`, `*.key`) to `.gitignore` to prevent secret leakage (GDPR / HIPAA compliance).
- Twilio credentials stored in `.env` only — never committed to repository
