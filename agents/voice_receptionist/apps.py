from django.apps import AppConfig


class VoiceReceptionistConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.voice_receptionist"
    verbose_name = "AI Voice Receptionist"

    def ready(self):
        import sys
        # Skip during management commands — DB tables don't exist yet
        _management_commands = {"migrate", "makemigrations", "collectstatic", "shell", "test", "check"}
        if sys.argv and len(sys.argv) > 1 and sys.argv[1] in _management_commands:
            return
        # Guard against double-start in dev (reloader forks the process)
        import os
        if os.environ.get("RUN_MAIN") != "true":
            from .scheduler import start_scheduler
            start_scheduler()
