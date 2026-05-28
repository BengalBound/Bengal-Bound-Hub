from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactViewSet, InteractionViewSet

app_name = "crux"

router = DefaultRouter()
router.register(r"contacts", ContactViewSet, basename="contacts")
router.register(r"interactions", InteractionViewSet, basename="interactions")

urlpatterns = [
    path("", include(router.urls)),
]
