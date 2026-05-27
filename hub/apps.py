from django.apps import AppConfig


class HubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hub'
    label = 'bredbound'  # keeps existing DB tables and migration graph intact

    def ready(self):
        import hub.signals  # noqa: F401 — registers signal handlers
