from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'video_concierge'

router = DefaultRouter()
router.register(r'sessions', views.VideoSessionViewSet, basename='sessions')

urlpatterns = [
    path('', include(router.urls)),
]
