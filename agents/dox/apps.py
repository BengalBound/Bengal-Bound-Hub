from django.apps import AppConfig


class DoxConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.dox"
    verbose_name = "Dox — Documentation Agent"

    def ready(self):
        import agents.dox.signals  # noqa
