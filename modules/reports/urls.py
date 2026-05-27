from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.report_list, name='report_list'),
    path('<int:pk>/run/', views.report_run, name='report_run'),
    path('dashboards/', views.dashboards, name='dashboards'),
]
