from django.urls import path
from . import views

app_name = 'ai_analytics'

urlpatterns = [
    path('', views.index, name='index'),
    path('datasets/', views.datasets, name='datasets'),
    path('insights/', views.insights, name='insights'),
    path('kpis/', views.kpis, name='kpis'),
]
