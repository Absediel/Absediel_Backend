from rest_framework import serializers
from .models import ContactSubmission, QuotationSubmission

class ContactSubmissionSerializer(serializers.ModelSerializer):
    serviceInterest = serializers.CharField(source='service_interest')

    class Meta:
        model = ContactSubmission
        fields = ['id', 'name', 'email', 'phone', 'serviceInterest', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']

class QuotationSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationSubmission
        fields = ['id', 'name', 'company', 'email', 'phone', 'services', 'timeline', 'budget', 'features', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']
