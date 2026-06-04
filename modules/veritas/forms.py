from django import forms
from .models import ClientApplication, KYBDocument

class ClientApplicationForm(forms.ModelForm):
    class Meta:
        model = ClientApplication
        fields = ['company_legal_name', 'registration_number', 'vat_number', 'jurisdiction']
        widgets = {
            'company_legal_name': forms.TextInput(attrs={'class': 'form-control form-control-premium', 'placeholder': 'e.g. Neurolink IT Ltd'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control form-control-premium', 'placeholder': 'Company Registration Number'}),
            'vat_number': forms.TextInput(attrs={'class': 'form-control form-control-premium', 'placeholder': 'Tax ID / EIN / VAT'}),
            'jurisdiction': forms.TextInput(attrs={'class': 'form-control form-control-premium', 'placeholder': 'Country / State'}),
        }

class KYBDocumentForm(forms.ModelForm):
    class Meta:
        model = KYBDocument
        fields = ['document_type', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select form-control-premium'}),
            'file': forms.FileInput(attrs={'class': 'form-control form-control-premium'}),
        }
