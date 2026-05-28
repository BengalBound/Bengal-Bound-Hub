from django.apps import AppConfig


class ContentStrategistConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.content_strategist"
    verbose_name = "Serea Content — Content Strategist"

    def ready(self):
        import agents.content_strategist.signals  # noqa
