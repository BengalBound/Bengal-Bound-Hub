from django.urls import path
from . import views

app_name = 're_marketing'

urlpatterns = [
    path('<slug:slug>/', views.marketing_home, name='home'),
    path('<slug:slug>/flyers/', views.flyer_list, name='flyer_list'),
    path('<slug:slug>/campaigns/', views.campaign_list, name='campaign_list'),
    path('<slug:slug>/social/', views.social_posts, name='social_posts'),
]
