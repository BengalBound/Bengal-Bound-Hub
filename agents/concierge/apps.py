from django.apps import AppConfig


class ConciergeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.concierge"
    verbose_name = "AI Concierge"

    def ready(self):
        import agents.concierge.signals  # noqa
