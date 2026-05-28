from django.apps import AppConfig


class VoiceReceptionistConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.voice_receptionist"
    verbose_name = "AI Voice Receptionist"

    def ready(self):
        # Start APScheduler background jobs when Django boots
        # Guard against double-start in dev (reloader forks the process)
        import os
        if os.environ.get("RUN_MAIN") != "true":
            from .scheduler import start_scheduler
            start_scheduler()
