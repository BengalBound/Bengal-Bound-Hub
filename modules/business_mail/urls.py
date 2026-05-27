from django.urls import path
from . import views

app_name = 'business_mail'

urlpatterns = [
    path('', views.mail_home, name='mail_home'),
    path('compose/', views.mail_compose, name='mail_compose'),
    path('accounts/', views.mail_account_manage, name='mail_account_manage'),
    path('<int:account_id>/', views.mail_inbox, name='mail_inbox'),
    path('<int:account_id>/<int:msg_id>/', views.mail_view, name='mail_view'),
]
