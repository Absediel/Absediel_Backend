import logging
import urllib.request
import json
import os
from django.conf import settings
from rest_framework.decorators import api_view, throttle_classes
from .throttling import EmailRateThrottle
from rest_framework.response import Response
from rest_framework import status
from .serializers import ContactSubmissionSerializer

logger = logging.getLogger(__name__)

def send_resend_email(to_email, subject, body):
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.error("RESEND_API_KEY environment variable is not set.")
        return False
        
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # By default, Resend free accounts send from onboarding@resend.dev
    from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    
    data = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "text": body
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status in [200, 201, 202]
    except Exception as e:
        logger.error(f"Failed to send email via Resend: {e}")
        return False

@api_view(['POST'])
@throttle_classes([EmailRateThrottle])
def contact_submit(request):
    serializer = ContactSubmissionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Save submission
    try:
        submission = serializer.save()
    except Exception as e:
        logger.error(f"Error saving submission: {e}")
        return Response({'message': 'Failed to save contact submission to the database.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    name = submission.name
    email = submission.email
    phone = submission.phone
    service_interest = submission.service_interest
    message = submission.message

    # Send Emails
    user_subject = "Thank you for contacting ABSEDIEL Technologies"
    user_body = f"""Hi {name},

Thank you for getting in touch with us! We have received your query regarding '{service_interest}'.
Our team will review your message and get back to you shortly.

Here is a summary of your inquiry:
- Service Interest: {service_interest}
- Message: {message}

Best regards,
Team ABSEDIEL"""

    admin_subject = f"New Contact Inquiry - {name}"
    admin_body = f"""You have received a new contact form submission on Absediel Technologies:

Name: {name}
Email: {email}
Phone: {phone}
Service Interest: {service_interest}
Message: {message}

Please respond to this request promptly."""

    email_sent_user = False
    email_sent_admin = False
    
    # User email confirmation
    try:
        email_sent_user = send_resend_email(email, user_subject, user_body)
    except Exception as e:
        logger.error(f"Failed to send confirmation email to user: {e}")
        
    # Admin email notification
    try:
        admin_recipient = getattr(settings, 'ADMIN_EMAIL', 'absedieltechnologies@gmail.com')
        email_sent_admin = send_resend_email(admin_recipient, admin_subject, admin_body)
    except Exception as e:
        logger.error(f"Failed to send notification email to admin: {e}")
        
    return Response({
        'message': 'Thank you for getting in touch! We will get back to you shortly.',
        'submission_id': submission.id,
        'email_sent_user': email_sent_user,
        'email_sent_admin': email_sent_admin
    }, status=status.HTTP_201_CREATED)
