from rest_framework import serializers
from .models import ContactSubmission

class ContactSubmissionSerializer(serializers.ModelSerializer):
    serviceInterest = serializers.CharField(source='service_interest')

    class Meta:
        model = ContactSubmission
        fields = ['id', 'name', 'email', 'phone', 'serviceInterest', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']
