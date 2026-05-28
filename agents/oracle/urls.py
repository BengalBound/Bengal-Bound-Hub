from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WebsiteViewSet, SEOIssueViewSet

app_name = 'oracle'
router = DefaultRouter()
router.register(r"websites", WebsiteViewSet, basename="website")
router.register(r"issues", SEOIssueViewSet, basename="seo-issue")

urlpatterns = [path("", include(router.urls))]