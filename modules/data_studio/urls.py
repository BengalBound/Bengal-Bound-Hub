from django.urls import path
from . import views

app_name = 'data_studio'

urlpatterns = [
    path('<slug:slug>/', views.studio_home, name='home'),
    path('<slug:slug>/datasets/', views.dataset_list, name='datasets'),
    path('<slug:slug>/datasets/<int:dataset_id>/', views.dataset_detail, name='dataset_detail'),
    path('<slug:slug>/charts/', views.chart_gallery, name='charts'),
]
