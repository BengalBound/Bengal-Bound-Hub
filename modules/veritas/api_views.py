from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ClientApplication, KYBDocument, SanctionsCheck, ClientAgreement
from .serializers import ClientApplicationSerializer, KYBDocumentSerializer, ClientAgreementSerializer
from django.utils import timezone
import hashlib

class VeritasClientViewSet(viewsets.ModelViewSet):
    """
    Client-facing API for KYB onboarding.
    Endpoints:
    - POST /apply/
    - POST /apply/{id}/documents/
    - GET /apply/{id}/status/
    - POST /apply/{id}/sign/{doc_type}/
    """
    serializer_class = ClientApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ClientApplication.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        # Create default agreements to sign
        app = serializer.instance
        for doc_type, _ in ClientAgreement.DOC_TYPES:
            ClientAgreement.objects.create(
                application=app,
                agreement_type=doc_type,
                version='v1.0'
            )

    @action(detail=True, methods=['post'])
    def documents(self, request, pk=None):
        application = self.get_object()
        serializer = KYBDocumentSerializer(data=request.data)
        if serializer.is_valid():
            doc = serializer.save(application=application)
            # Future: trigger OCR task here
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        application = self.get_object()
        return Response({'status': application.status, 'risk_level': application.risk_level})

    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        application = self.get_object()
        doc_type = request.data.get('doc_type')
        if not doc_type:
            return Response({'error': 'doc_type is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            agreement = ClientAgreement.objects.get(application=application, agreement_type=doc_type)
        except ClientAgreement.DoesNotExist:
            return Response({'error': 'Agreement not found'}, status=status.HTTP_404_NOT_FOUND)

        if agreement.signed:
            return Response({'error': 'Already signed'}, status=status.HTTP_400_BAD_REQUEST)

        agreement.signed = True
        agreement.signed_at = timezone.now()
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        agreement.ip_address = ip

        # Generate a simple signature hash (content mock)
        content_to_sign = f"{agreement.agreement_type}-{agreement.version}-{agreement.signed_at.isoformat()}-{ip}"
        agreement.signature_hash = hashlib.sha256(content_to_sign.encode('utf-8')).hexdigest()
        agreement.save()
        
        return Response({'status': 'signed', 'signature_hash': agreement.signature_hash})


class VeritasAdminViewSet(viewsets.ModelViewSet):
    """
    Admin-facing API for ops team.
    """
    queryset = ClientApplication.objects.all().order_by('-submitted_at')
    serializer_class = ClientApplicationSerializer
    
    # Needs to be restricted to admins, omitting custom permission for now
    # permission_classes = [IsAdminUser] 
    
    @action(detail=True, methods=['patch'])
    def approve(self, request, pk=None):
        application = self.get_object()
        application.status = 'approved'
        application.approved_at = timezone.now()
        application.reviewed_by = request.user.email if request.user.is_authenticated else 'system'
        application.save()
        return Response({'status': 'approved'})

    @action(detail=True, methods=['patch'])
    def reject(self, request, pk=None):
        application = self.get_object()
        reason = request.data.get('reason', '')
        if not reason:
            return Response({'error': 'rejection reason required'}, status=status.HTTP_400_BAD_REQUEST)
        
        application.status = 'rejected'
        application.rejection_reason = reason
        application.rejected_at = timezone.now()
        application.reviewed_by = request.user.email if request.user.is_authenticated else 'system'
        application.save()
        return Response({'status': 'rejected'})

    @action(detail=True, methods=['post'])
    def rescan(self, request, pk=None):
        # Trigger Celery rescan tasks
        return Response({'status': 'rescanning triggered'})
