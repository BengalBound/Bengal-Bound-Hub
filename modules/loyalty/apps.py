from django.apps import AppConfig


class LoyaltyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.loyalty'
    label = 'loyalty'
    verbose_name = 'Loyalty'
