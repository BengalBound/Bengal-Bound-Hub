from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import JobViewSet, JobQuoteViewSet, VanInventoryViewSet, CustomerSignatureViewSet

app_name = 'fsm_api'

router = DefaultRouter()
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'quotes', JobQuoteViewSet, basename='jobquote')
router.register(r'inventory', VanInventoryViewSet, basename='vaninventory')
router.register(r'signatures', CustomerSignatureViewSet, basename='customersignature')

urlpatterns = [
    path('', include(router.urls)),
]
