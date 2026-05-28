from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StoreViewSet, ProductViewSet

app_name = 'merch'
router = DefaultRouter()
router.register(r"stores", StoreViewSet, basename="store")
router.register(r"products", ProductViewSet, basename="product")

urlpatterns = [path("", include(router.urls))]