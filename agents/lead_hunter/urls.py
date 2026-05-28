from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProspectViewSet, OutreachSequenceViewSet

app_name = "lead_hunter"

router = DefaultRouter()
router.register(r"prospects", ProspectViewSet, basename="prospects")
router.register(r"sequences", OutreachSequenceViewSet, basename="sequences")

urlpatterns = [
    path("", include(router.urls)),
]
