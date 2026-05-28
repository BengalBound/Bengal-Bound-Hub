from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, LeadViewSet

app_name = 'realt'
router = DefaultRouter()
router.register(r"properties", PropertyViewSet, basename="property")
router.register(r"leads", LeadViewSet, basename="realt-lead")

urlpatterns = [path("", include(router.urls))]
