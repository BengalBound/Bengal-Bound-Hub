from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'pitch_presenter'

router = DefaultRouter()
router.register(r'pitches', views.VideoPitchViewSet, basename='pitches')

urlpatterns = [
    path('', include(router.urls)),
]
