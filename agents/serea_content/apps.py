from django.apps import AppConfig


class SereaContentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.serea_content"
    verbose_name = "Serea Content — Content Strategist"

    def ready(self):
        import agents.serea_content.signals  # noqa
