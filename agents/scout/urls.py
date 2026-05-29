from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompetitorViewSet, CompetitorChangeViewSet

app_name = 'scout'
router = DefaultRouter()
router.register(r"competitors", CompetitorViewSet, basename="competitor")
router.register(r"changes", CompetitorChangeViewSet, basename="competitor-change")

urlpatterns = [path("", include(router.urls))]
