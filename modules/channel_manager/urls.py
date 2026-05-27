from django.urls import path
from . import views

app_name = 'channel_manager'

urlpatterns = [
    path('', views.cm_home, name='home'),
    path('channels/', views.channel_list, name='channels'),
    path('rates/', views.rate_plans, name='rates'),
    path('availability/', views.availability, name='availability'),
    path('sync/', views.sync_log, name='sync_log'),
]
