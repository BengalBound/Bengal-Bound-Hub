from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import BusinessInstanceViewSet, BusinessEmployeeViewSet

app_name = 'hub_api'

router = DefaultRouter()
router.register(r'businesses', BusinessInstanceViewSet, basename='business')
router.register(r'employees', BusinessEmployeeViewSet, basename='businessemployee')

urlpatterns = [
    path('', include(router.urls)),
]
