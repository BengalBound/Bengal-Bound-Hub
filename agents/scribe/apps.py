from django.apps import AppConfig

class ScribeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agents.scribe'
    verbose_name = 'AI Notetaker (Scribe Agent)'

    def ready(self):
        import agents.scribe.signals  # noqa
