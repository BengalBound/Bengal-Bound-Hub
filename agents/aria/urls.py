from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupportTicketViewSet, TicketResponseViewSet

app_name = "aria"

router = DefaultRouter()
router.register(r"tickets", SupportTicketViewSet, basename="tickets")
router.register(r"responses", TicketResponseViewSet, basename="responses")

urlpatterns = [
    path("", include(router.urls)),
]
