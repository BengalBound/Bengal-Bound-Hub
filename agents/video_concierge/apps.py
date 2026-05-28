from django.apps import AppConfig

class VideoConciergeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agents.video_concierge'
    verbose_name = 'AI Video Concierge (Chloe Agent)'

    def ready(self):
        import agents.video_concierge.signals  # noqa
