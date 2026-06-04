from django.db import models
from django.conf import settings

class ClientApplication(models.Model):
    STATUS = [
        ('submitted','Submitted'),('documents_pending','Documents Pending'),
        ('under_review','Under Review — Automated'),('human_review','Human Review'),
        ('approved','Approved'),('rejected','Rejected'),('suspended','Suspended')
    ]
    RISK_LEVEL = [('green','Green'),('amber','Amber'),('red','Red')]

    user                = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company_legal_name  = models.CharField(max_length=500)
    registration_number = models.CharField(max_length=200)
    jurisdiction        = models.CharField(max_length=100)   # Country/state
    registered_address  = models.TextField()
    incorporation_date  = models.DateField(null=True)
    business_type       = models.CharField(max_length=200)   # 'Agency', 'Clinic', etc.
    website             = models.URLField(blank=True)
    vat_number          = models.CharField(max_length=100, blank=True)
    director_name       = models.CharField(max_length=300)
    director_email      = models.EmailField()
    director_phone      = models.CharField(max_length=30)

    # Verification results
    registry_verified   = models.BooleanField(null=True)
    sanctions_clear     = models.BooleanField(null=True)
    aml_clear           = models.BooleanField(null=True)
    documents_verified  = models.BooleanField(null=True)
    risk_score          = models.IntegerField(null=True)         # 0–100
    risk_level          = models.CharField(max_length=10, choices=RISK_LEVEL, blank=True)
    gemini_risk_summary = models.TextField(blank=True)

    # Status
    status              = models.CharField(max_length=30, choices=STATUS, default='submitted')
    rejection_reason    = models.TextField(blank=True)
    reviewed_by         = models.CharField(max_length=200, blank=True)
    approved_at         = models.DateTimeField(null=True)
    rejected_at         = models.DateTimeField(null=True)
    submitted_at        = models.DateTimeField(auto_now_add=True)
    next_review_date    = models.DateField(null=True)           # Quarterly re-check

class KYBDocument(models.Model):
    DOC_TYPES = [
        ('incorporation','Certificate of Incorporation'),
        ('trade_license','Trade License'),
        ('vat_cert','VAT/Tax Certificate'),
        ('proof_address','Proof of Business Address'),
        ('director_passport','Director Passport'),
        ('director_id','Director National ID'),
        ('bank_statement','Bank Statement Header'),
    ]
    STATUS = [('pending','Pending'),('verified','Verified'),('rejected','Rejected')]

    application         = models.ForeignKey(ClientApplication, on_delete=models.CASCADE)
    document_type       = models.CharField(max_length=30, choices=DOC_TYPES)
    file                = models.FileField(upload_to='kyb/documents/')
    ocr_extracted_data  = models.JSONField(default=dict)    # AI-extracted fields
    ai_verification     = models.BooleanField(null=True)
    rejection_reason    = models.TextField(blank=True)
    status              = models.CharField(max_length=20, choices=STATUS, default='pending')
    uploaded_at         = models.DateTimeField(auto_now_add=True)
    verified_at         = models.DateTimeField(null=True)

class SanctionsCheck(models.Model):
    application         = models.ForeignKey(ClientApplication, on_delete=models.CASCADE)
    checked_entity      = models.CharField(max_length=500)  # Company or director name
    list_checked        = models.CharField(max_length=100)  # 'OFAC', 'UN', 'EU', etc.
    match_found         = models.BooleanField(default=False)
    match_score         = models.FloatField(null=True)      # Fuzzy match score
    match_detail        = models.TextField(blank=True)
    checked_at          = models.DateTimeField(auto_now_add=True)

class ClientAgreement(models.Model):
    DOC_TYPES = [('tos','Terms of Service'),('dpa','Data Processing Agreement'),
                 ('aup','Acceptable Use Policy'),('ai_ethics','AI Ethics Acknowledgement')]
    application         = models.ForeignKey(ClientApplication, on_delete=models.CASCADE)
    agreement_type      = models.CharField(max_length=20, choices=DOC_TYPES)
    version             = models.CharField(max_length=20)   # e.g. 'v2.1'
    signed              = models.BooleanField(default=False)
    signed_at           = models.DateTimeField(null=True)
    ip_address          = models.GenericIPAddressField(null=True)
    signature_hash      = models.CharField(max_length=64)   # SHA-256 of signed content + timestamp
