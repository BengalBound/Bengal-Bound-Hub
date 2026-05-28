from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VendorViewSet, RFQViewSet

app_name = 'payload'
router = DefaultRouter()
router.register(r"vendors", VendorViewSet, basename="vendor")
router.register(r"rfqs", RFQViewSet, basename="rfq")

urlpatterns = [path("", include(router.urls))]