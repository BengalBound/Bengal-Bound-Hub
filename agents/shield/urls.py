from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ITTicketViewSet, KnowledgeArticleViewSet

app_name = 'shield'
router = DefaultRouter()
router.register(r"tickets", ITTicketViewSet, basename="it-ticket")
router.register(r"knowledge", KnowledgeArticleViewSet, basename="knowledge-article")

urlpatterns = [path("", include(router.urls))]