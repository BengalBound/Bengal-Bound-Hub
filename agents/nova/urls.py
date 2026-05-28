from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DataSourceViewSet, DataQueryViewSet

app_name = 'nova'
router = DefaultRouter()
router.register(r"sources", DataSourceViewSet, basename="data-source")
router.register(r"queries", DataQueryViewSet,  basename="data-query")

urlpatterns = [path("", include(router.urls))]