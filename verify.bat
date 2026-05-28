@echo off
REM Automated verification script for NIST SP 800-218

echo Running linter (ruff)...
ruff check . --select E,F,W --ignore E501

echo Running automated test suite...
python manage.py test --settings=bengalbound_core.settings.testing

echo Verification complete!
