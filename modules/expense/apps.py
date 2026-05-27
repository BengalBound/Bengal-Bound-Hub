from django.apps import AppConfig


class ExpenseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.expense'
    label = 'expense'
    verbose_name = 'Expense'
