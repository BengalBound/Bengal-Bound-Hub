from django.urls import path
from . import views

app_name = 'planogram'

urlpatterns = [
    path('<slug:slug>/', views.planogram_home, name='home'),
    path('<slug:slug>/layouts/<int:layout_id>/', views.layout_detail, name='layout_detail'),
]
