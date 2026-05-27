from django.apps import AppConfig


class EmailMarketingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.email_marketing'
    label = 'email_marketing'
    verbose_name = 'Email Marketing'
