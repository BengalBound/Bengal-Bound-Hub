from django.urls import path
from . import views

app_name = 'invoicing'

urlpatterns = [
    path('', views.index, name='index'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/new/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('clients/', views.clients, name='clients'),
]
