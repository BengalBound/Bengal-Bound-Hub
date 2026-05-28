from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContentPieceViewSet, CampaignViewSet

app_name = "serea_content"

router = DefaultRouter()
router.register(r"content",   ContentPieceViewSet, basename="content-piece")
router.register(r"campaigns", CampaignViewSet,     basename="campaign")

urlpatterns = [path("", include(router.urls))]
