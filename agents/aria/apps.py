from django.apps import AppConfig

class AriaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.aria"
    verbose_name = "Aria — Customer Support"

    def ready(self):
        import agents.aria.signals  # noqa
