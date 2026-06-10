from rest_framework import serializers
from .models import ClientApplication, KYBDocument, SanctionsCheck, ClientAgreement

class KYBDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYBDocument
        fields = ['id', 'document_type', 'file', 'status', 'rejection_reason', 'uploaded_at', 'verified_at']
        read_only_fields = ['status', 'rejection_reason', 'uploaded_at', 'verified_at']

class SanctionsCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = SanctionsCheck
        fields = '__all__'
        read_only_fields = ['application', 'checked_entity', 'list_checked', 'match_found', 'match_score', 'match_detail', 'checked_at']

class ClientAgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientAgreement
        fields = ['id', 'agreement_type', 'version', 'signed', 'signed_at', 'ip_address']
        read_only_fields = ['signed', 'signed_at', 'ip_address', 'version']

class ClientApplicationSerializer(serializers.ModelSerializer):
    documents = KYBDocumentSerializer(source='kybdocument_set', many=True, read_only=True)
    agreements = ClientAgreementSerializer(source='clientagreement_set', many=True, read_only=True)
    sanctions_checks = SanctionsCheckSerializer(source='sanctionscheck_set', many=True, read_only=True)
    
    class Meta:
        model = ClientApplication
        fields = [
            'id', 'company_legal_name', 'registration_number', 'jurisdiction', 
            'registered_address', 'incorporation_date', 'business_type', 'website', 
            'vat_number', 'director_name', 'director_email', 'director_phone',
            'status', 'rejection_reason', 'risk_score', 'risk_level',
            'documents', 'agreements', 'sanctions_checks', 'submitted_at'
        ]
        read_only_fields = ['status', 'rejection_reason', 'risk_score', 'risk_level', 'submitted_at']
