from django.urls import path
from . import views

app_name = 'veritas_user'

urlpatterns = [
    path('', views.kyb_apply_user, name='kyb_apply'),
    path('pending/', views.kyb_pending_user, name='kyb_pending'),
]
