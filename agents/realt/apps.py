from django.apps import AppConfig


class RealtConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.realt"
    verbose_name = "Realt — Real Estate Agent"

    def ready(self):
        import agents.realt.signals  # noqa
