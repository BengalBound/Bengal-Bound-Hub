from django.urls import path
from . import views

app_name = 'plm'

urlpatterns = [
    path('<slug:slug>/', views.plm_dashboard, name='dashboard'),
    path('<slug:slug>/products/', views.plm_products, name='products'),
    path('<slug:slug>/products/<int:product_id>/', views.plm_product_detail, name='product_detail'),
    path('<slug:slug>/ecos/', views.plm_ecos, name='ecos'),
    # Footwear shoe article routes
    path('<slug:slug>/shoe-articles/', views.shoe_articles, name='shoe_articles'),
    path('<slug:slug>/shoe-articles/<int:article_id>/', views.shoe_article_detail, name='shoe_article_detail'),
]
