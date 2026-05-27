from django.urls import path
from . import views

app_name = 'travel_desk'

urlpatterns = [
    path('', views.td_home, name='home'),
    path('accounts/', views.accounts, name='accounts'),
    path('policy/', views.policy, name='policy'),
    path('requests/', views.requests, name='requests'),
    path('requests/<int:req_id>/', views.request_detail, name='request_detail'),
]
