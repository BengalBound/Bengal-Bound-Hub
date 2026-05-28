from django.apps import AppConfig


class KaiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.kai"
    verbose_name = "Kai — DevOps"

    def ready(self):
        import agents.kai.signals  # noqa
