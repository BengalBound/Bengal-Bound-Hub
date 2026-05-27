from django.urls import path
from . import views

app_name = 'financials'

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.financial_dashboard, name='financial_dashboard'),
    path('reports/', views.report_list, name='report_list'),
    path('reports/submit/', views.report_submit, name='report_submit'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('expenses/log/', views.log_expense, name='log_expense'),
    path('expenses/my/', views.my_expenses, name='my_expenses'),
    path('expenses/overview/', views.expense_overview, name='expense_overview'),
]
