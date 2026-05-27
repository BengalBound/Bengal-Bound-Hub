from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.index, name='index'),
    path('periods/', views.pay_periods, name='pay_periods'),
    path('payslips/', views.payslips, name='payslips'),
    path('structures/', views.structures, name='structures'),
]
