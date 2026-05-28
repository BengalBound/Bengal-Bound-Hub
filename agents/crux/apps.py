from django.apps import AppConfig

class CruxConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.crux"
    verbose_name = "Crux — CRM Manager"

    def ready(self):
        import agents.crux.signals  # noqa
