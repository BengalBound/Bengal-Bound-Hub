from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LegalDocumentViewSet, ClauseViewSet

app_name = 'sage'
router = DefaultRouter()
router.register(r"documents", LegalDocumentViewSet, basename="legal-document")
router.register(r"clauses", ClauseViewSet, basename="clause")

urlpatterns = [path("", include(router.urls))]
