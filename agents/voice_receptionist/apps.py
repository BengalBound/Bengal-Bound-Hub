from django.apps import AppConfig


class VoiceReceptionistConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.voice_receptionist"
    verbose_name = "AI Voice Receptionist"

    def ready(self):
        import os
        import sys
        # Skip during management commands — DB tables don't exist yet
        _management_commands = {
            "migrate", "makemigrations", "collectstatic", "shell", "test", "check",
            "seed_modules", "seed_agents", "createsuperuser", "dbshell", "showmigrations",
            "sqlmigrate", "flush", "inspectdb"
        }
        if sys.argv and len(sys.argv) > 1 and sys.argv[1] in _management_commands:
            return
        # Skip during tests (pytest, unittest, etc.)
        if any(x in sys.argv[0] or (len(sys.argv) > 1 and x in sys.argv[1]) for x in ("pytest", "test")):
            return
        if "test" in sys.argv or "pytest" in sys.modules:
            return
        # Skip on Cloud Run — ephemeral containers can't run reliable cron jobs; use Celery Beat instead
        if os.environ.get("K_SERVICE"):
            return
        # Guard against double-start in dev (reloader forks the process)
        if os.environ.get("RUN_MAIN") != "true":
            from .scheduler import start_scheduler
            start_scheduler()
