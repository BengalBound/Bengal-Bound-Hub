from django.urls import path
from . import views

app_name = 'veritas'

urlpatterns = [
    path('', views.kyb_list, name='kyb_list'),
    path('<int:app_id>/', views.kyb_detail, name='kyb_detail'),
    path('<int:app_id>/approve/', views.kyb_approve, name='kyb_approve'),
    path('<int:app_id>/reject/', views.kyb_reject, name='kyb_reject'),
]
