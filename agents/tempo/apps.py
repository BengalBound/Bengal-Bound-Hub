from django.apps import AppConfig


class TempoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.tempo"
    verbose_name = "Tempo — Event Management"

    def ready(self):
        import agents.tempo.signals  # noqa
