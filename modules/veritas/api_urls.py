from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import VeritasClientViewSet, VeritasAdminViewSet

app_name = 'veritas_api'

router = DefaultRouter()
router.register(r'applications', VeritasAdminViewSet, basename='applications')
router.register(r'apply', VeritasClientViewSet, basename='apply')

urlpatterns = [
    path('', include(router.urls)),
]
