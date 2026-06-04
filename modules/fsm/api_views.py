from rest_framework import viewsets, permissions
from .models import Job, JobQuote, VanInventory, CustomerSignature
from .serializers import JobSerializer, JobQuoteSerializer, VanInventorySerializer, CustomerSignatureSerializer
from hub.models import BusinessInstance

class FSMBaseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        slug = self.request.query_params.get('business')
        if slug:
            return self.queryset.filter(business__slug=slug)
        return self.queryset.filter(business__owner=self.request.user)

class JobViewSet(FSMBaseViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer

class JobQuoteViewSet(FSMBaseViewSet):
    queryset = JobQuote.objects.all()
    serializer_class = JobQuoteSerializer

class VanInventoryViewSet(FSMBaseViewSet):
    queryset = VanInventory.objects.all()
    serializer_class = VanInventorySerializer

class CustomerSignatureViewSet(FSMBaseViewSet):
    queryset = CustomerSignature.objects.all()
    serializer_class = CustomerSignatureSerializer
