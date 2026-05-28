from django.apps import AppConfig


class MedibookConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.medibook"
    verbose_name = "Medibook — Medical Scheduling"

    def ready(self):
        import agents.medibook.signals  # noqa
