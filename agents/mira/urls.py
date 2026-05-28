from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientHealthViewSet, SuccessEmailViewSet

app_name = "mira"

router = DefaultRouter()
router.register(r"health", ClientHealthViewSet, basename="health")
router.register(r"emails", SuccessEmailViewSet, basename="emails")

urlpatterns = [
    path("", include(router.urls)),
]
