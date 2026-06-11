from django.urls import path
from . import views

app_name = 'tax_compliance'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
