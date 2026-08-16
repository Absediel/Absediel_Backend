import logging
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.decorators import api_view, throttle_classes
from .throttling import EmailRateThrottle
from rest_framework.response import Response
from rest_framework import status
from .serializers import ContactSubmissionSerializer

logger = logging.getLogger(__name__)

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
        send_mail(
            subject=user_subject,
            message=user_body,
            from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@absediel.com',
            recipient_list=[email],
            fail_silently=False,
        )
        email_sent_user = True
    except Exception as e:
        logger.error(f"Failed to send confirmation email to user: {e}")
        print(f"SMTP Error user email: {e}")
        
    # Admin email notification
    try:
        admin_recipient = getattr(settings, 'ADMIN_EMAIL', 'absedieltechnologies@gmail.com')
        send_mail(
            subject=admin_subject,
            message=admin_body,
            from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@absediel.com',
            recipient_list=[admin_recipient],
            fail_silently=False,
        )
        email_sent_admin = True
    except Exception as e:
        logger.error(f"Failed to send notification email to admin: {e}")
        print(f"SMTP Error admin email: {e}")
        
    return Response({
        'message': 'Thank you for getting in touch! We will get back to you shortly.',
        'submission_id': submission.id,
        'email_sent_user': email_sent_user,
        'email_sent_admin': email_sent_admin
    }, status=status.HTTP_201_CREATED)
