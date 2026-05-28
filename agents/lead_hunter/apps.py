from django.apps import AppConfig

class LeadHunterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents.lead_hunter"
    verbose_name = "Lead Hunter — B2B Prospector"

    def ready(self):
        import agents.lead_hunter.signals  # noqa
