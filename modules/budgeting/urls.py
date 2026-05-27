from django.urls import path
from . import views

app_name = 'budgeting'

urlpatterns = [
    path('', views.index, name='index'),
    path('periods/', views.periods, name='periods'),
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/<int:pk>/', views.budget_detail, name='budget_detail'),
]
