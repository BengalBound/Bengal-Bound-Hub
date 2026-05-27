from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    path('', views.index, name='index'),
    path('accounts/', views.chart_of_accounts, name='chart_of_accounts'),
    path('journal/', views.journal_entries, name='journal_entries'),
    path('journal/new/', views.journal_entry_create, name='journal_entry_create'),
    path('tax-rates/', views.tax_rates, name='tax_rates'),
]
