from django.apps import AppConfig


class FluxConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.flux"
    verbose_name = "Flux — Supply Chain Agent"

    def ready(self):
        import agents.flux.signals  # noqa
