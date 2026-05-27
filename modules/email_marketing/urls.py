from django.urls import path
from . import views

app_name = 'email_marketing'

urlpatterns = [
    path('', views.index, name='index'),
    path('campaigns/', views.campaign_list, name='campaign_list'),
    path('campaigns/new/', views.campaign_create, name='campaign_create'),
    path('campaigns/<int:pk>/', views.campaign_detail, name='campaign_detail'),
    path('lists/', views.email_lists, name='email_lists'),
    path('lists/<int:list_id>/subscribers/', views.subscribers, name='subscribers'),
]
