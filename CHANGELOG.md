# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Testing Environment**: Added `bengalbound_core/settings/testing.py` to enforce strict environment separation (ISO/IEC 27001).
- **Verification Scripts**: Added `verify.sh` and `verify.bat` for automated testing and linting (NIST SP 800-218).
- **SBOM**: Generated `sbom.json` using CycloneDX to track all Python dependencies (EO 14028).

### Changed
- **Agent Mini-Platform**: Migrated all 30 agents to the new live `AgentInstance` architecture, upgrading them from standalone celery task runners to a robust platform tier system.
- **Repository Root Structure**: Consolidated scratch files (`test.py`, `scaffold_agents.py`, etc.) into a dedicated `scripts/` directory to declutter the root.

### Security
- **Data Protection**: Explicitly added certificates (`*.pem`, `*.key`) to `.gitignore` to prevent secret leakage (GDPR / HIPAA compliance).
