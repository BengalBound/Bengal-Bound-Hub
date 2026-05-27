from django.urls import path
from . import views

app_name = 'timetable'
urlpatterns = [
    path('<slug:slug>/', views.timetable_home, name='home'),
    path('<slug:slug>/rooms/', views.room_list, name='room_list'),
    path('<slug:slug>/sessions/', views.session_manage, name='session_manage'),
]
