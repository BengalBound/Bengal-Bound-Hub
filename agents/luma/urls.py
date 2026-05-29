from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BrandMentionViewSet, PressReleaseViewSet

app_name = 'luma'
router = DefaultRouter()
router.register(r"mentions", BrandMentionViewSet, basename="brand-mention")
router.register(r"press-releases", PressReleaseViewSet, basename="press-release")

urlpatterns = [path("", include(router.urls))]
