from rest_framework import serializers
from .models import Job, JobQuote, JobQuoteItem, VanInventory, CustomerSignature

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'

class JobQuoteItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobQuoteItem
        fields = '__all__'

class JobQuoteSerializer(serializers.ModelSerializer):
    items = JobQuoteItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = JobQuote
        fields = '__all__'

class VanInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VanInventory
        fields = '__all__'

class CustomerSignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerSignature
        fields = '__all__'
