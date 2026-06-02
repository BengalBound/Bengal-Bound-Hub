from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import BusinessInstance, BusinessEmployee, HubPlanConfig
from .serializers import BusinessInstanceSerializer, BusinessEmployeeSerializer, HubPlanConfigSerializer

class BusinessInstanceViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessInstanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see businesses they own or belong to
        user = self.request.user
        owned = BusinessInstance.objects.filter(owner=user)
        member = BusinessInstance.objects.filter(businessemployee__user=user)
        return (owned | member).distinct()

    @action(detail=True, methods=['get'])
    def team(self, request, pk=None):
        business = self.get_object()
        users = business.employees.all()
        serializer = BusinessEmployeeSerializer(users, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def subscription(self, request, pk=None):
        business = self.get_object()
        plan = business.hubplanconfig_set.filter(is_active=True).first()
        if plan:
            serializer = HubPlanConfigSerializer(plan)
            return Response(serializer.data)
        return Response({'detail': 'No active subscription found.'}, status=404)

class BusinessEmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessEmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see other users in their business instances
        user = self.request.user
        businesses = BusinessInstance.objects.filter(businessemployee__user=user)
        return BusinessEmployee.objects.filter(business__in=businesses).distinct()
