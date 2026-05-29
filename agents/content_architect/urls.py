from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContentCalendarViewSet, CalendarEntryViewSet

app_name = 'content_architect'
router = DefaultRouter()
router.register(r"calendars", ContentCalendarViewSet, basename="content-calendar")
router.register(r"entries",   CalendarEntryViewSet,   basename="calendar-entry")

urlpatterns = [path("", include(router.urls))]
