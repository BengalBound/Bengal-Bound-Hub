from django.apps import AppConfig


class MerchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.merch"
    verbose_name = "Merch — eCommerce Agent"

    def ready(self):
        import agents.merch.signals  # noqa
