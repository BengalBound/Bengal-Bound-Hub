from django.apps import AppConfig

class PitchPresenterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agents.pitch_presenter'
    verbose_name = 'AI Pitch Presenter (Video Agent)'

    def ready(self):
        import agents.pitch_presenter.signals  # noqa
