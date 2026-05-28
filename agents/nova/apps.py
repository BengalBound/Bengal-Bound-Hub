from django.apps import AppConfig


class NovaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.nova"
    verbose_name = "Nova — Data Analyst"

    def ready(self):
        import agents.nova.signals  # noqa
