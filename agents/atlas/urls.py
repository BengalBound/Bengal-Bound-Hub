from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExecTaskViewSet, MeetingBriefViewSet

app_name = 'atlas'
router = DefaultRouter()
router.register(r"tasks", ExecTaskViewSet, basename="exec-task")
router.register(r"briefs", MeetingBriefViewSet, basename="meeting-brief")

urlpatterns = [path("", include(router.urls))]
