from django.urls import path
from . import views

app_name = 'business_calendar'

urlpatterns = [
    path('', views.calendar_home, name='calendar_home'),
    path('api/events/', views.calendar_events_api, name='events_api'),
    path('event/new/', views.event_create, name='event_create'),
    path('event/<int:pk>/', views.event_detail, name='event_detail'),
    path('manage/', views.calendar_manage, name='calendar_manage'),
]
