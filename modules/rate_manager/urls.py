from django.urls import path
from . import views

app_name = 'rate_manager'

urlpatterns = [
    path('', views.rm_home, name='home'),
    path('seasons/', views.seasons, name='seasons'),
    path('rates/', views.base_rates, name='base_rates'),
    path('yield/', views.yield_rules, name='yield_rules'),
    path('offers/', views.special_offers, name='special_offers'),
]
