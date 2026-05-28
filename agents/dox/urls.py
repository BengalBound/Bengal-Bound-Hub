from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentationProjectViewSet, DocPageViewSet

app_name = 'dox'
router = DefaultRouter()
router.register(r"projects", DocumentationProjectViewSet, basename="doc-project")
router.register(r"pages", DocPageViewSet, basename="doc-page")

urlpatterns = [path("", include(router.urls))]