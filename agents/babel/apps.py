from django.apps import AppConfig


class BabelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.babel"
    verbose_name = "Babel — Translation Agent"

    def ready(self):
        import agents.babel.signals  # noqa
