from django.apps import AppConfig


class TaskBoardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.task_board'
    label = 'task_board'
    verbose_name = 'Task Board'
