from django.urls import path
from . import views

app_name = 'video_meet'

urlpatterns = [
    path('', views.meet_home, name='meet_home'),
    path('schedule/', views.meet_schedule, name='meet_schedule'),
    path('<int:pk>/', views.meet_detail, name='meet_detail'),
    path('rooms/', views.room_manage, name='room_manage'),
]
