from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PipelineViewSet, IncidentViewSet

app_name = 'kai'
router = DefaultRouter()
router.register(r"pipelines", PipelineViewSet, basename="pipeline")
router.register(r"incidents", IncidentViewSet, basename="incident")

urlpatterns = [path("", include(router.urls))]