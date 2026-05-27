from django.apps import AppConfig


class OrderMgmtConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.order_mgmt'
    label = 'order_mgmt'
    verbose_name = 'Order Mgmt'
