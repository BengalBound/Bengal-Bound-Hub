from django.apps import AppConfig


class SereaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'serea'
    verbose_name = 'Serea — AI Social Media Moderator'

    def ready(self):
        import serea.signals  # noqa: F401 — registers the post_save receiver
