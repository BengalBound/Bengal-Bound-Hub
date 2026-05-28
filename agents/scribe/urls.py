from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'scribe'

router = DefaultRouter()
router.register(r'meetings', views.MeetingViewSet, basename='meetings')

urlpatterns = [
    path('', include(router.urls)),
]
