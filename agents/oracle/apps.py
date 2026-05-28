from django.apps import AppConfig


class OracleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.oracle"
    verbose_name = "Oracle — SEO Agent"

    def ready(self):
        import agents.oracle.signals  # noqa
