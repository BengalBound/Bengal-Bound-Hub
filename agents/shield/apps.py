from django.apps import AppConfig


class ShieldConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.shield"
    verbose_name = "Shield — IT Helpdesk"

    def ready(self):
        import agents.shield.signals  # noqa
