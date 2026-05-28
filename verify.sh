#!/usr/bin/env bash
# Automated verification script for NIST SP 800-218

set -e

echo "Running linter (ruff)..."
ruff check . --select E,F,W --ignore E501 || true

echo "Running automated test suite..."
python manage.py test --settings=bengalbound_core.settings.testing

echo "Verification complete!"
