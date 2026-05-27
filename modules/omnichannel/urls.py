from django.urls import path
from . import views

app_name = 'omnichannel'

urlpatterns = [
    path('<slug:slug>/', views.omnichannel_home, name='home'),
    path('<slug:slug>/channels/', views.channel_list, name='channel_list'),
    path('<slug:slug>/channels/<int:channel_id>/', views.channel_detail, name='channel_detail'),
]
