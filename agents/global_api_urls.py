from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import AgentCatalogViewSet

app_name = 'agents_global_api'

router = DefaultRouter()
router.register(r'catalog', AgentCatalogViewSet, basename='catalog')

urlpatterns = [
    path('', include(router.urls)),
]
