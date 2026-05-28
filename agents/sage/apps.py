from django.apps import AppConfig


class SageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.sage"
    verbose_name = "Sage — Legal AI"

    def ready(self):
        import agents.sage.signals  # noqa
