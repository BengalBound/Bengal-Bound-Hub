from django.apps import AppConfig


class HeraConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.hera"
    verbose_name = "Hera — HR Agent"

    def ready(self):
        import agents.hera.signals  # noqa
