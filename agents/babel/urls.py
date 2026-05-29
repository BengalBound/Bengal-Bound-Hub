from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TranslationJobViewSet, TranslationOutputViewSet

app_name = 'babel'
router = DefaultRouter()
router.register(r"jobs", TranslationJobViewSet, basename="translation-job")
router.register(r"outputs", TranslationOutputViewSet, basename="translation-output")

urlpatterns = [path("", include(router.urls))]
