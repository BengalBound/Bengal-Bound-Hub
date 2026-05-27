from django.apps import AppConfig

class DocsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.docs'
    label = 'docs'
    verbose_name = 'Docs'
