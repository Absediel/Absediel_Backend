import logging
import urllib.request
import urllib.error
import json
import os
from django.conf import settings
from rest_framework.decorators import api_view, throttle_classes
from .throttling import EmailRateThrottle
from rest_framework.response import Response
from rest_framework import status
from .models import ContactSubmission, QuotationSubmission
from .serializers import ContactSubmissionSerializer, QuotationSubmissionSerializer

logger = logging.getLogger(__name__)

def send_resend_email(to_email, subject, body):
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.warning("RESEND_API_KEY environment variable is not set.")
        return False
        
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
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
        with urllib.request.urlopen(req, timeout=8) as response:
            return response.status in [200, 201, 202]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        logger.error(f"Failed to send email via Resend: {e}. Response: {error_body}")
        return False
    except Exception as e:
        logger.error(f"Failed to send email via Resend: {e}")
        return False

def send_email_notification(to_email, subject, body):
    """
    Sends email via Resend if RESEND_API_KEY exists,
    otherwise falls back to Django SMTP (configured in settings.py).
    """
    if os.getenv("RESEND_API_KEY"):
        if send_resend_email(to_email, subject, body):
            return True
        logger.warning("Resend delivery failed or unconfigured, attempting Django SMTP fallback...")

    # Fallback to Django SMTP
    try:
        from django.core.mail import send_mail
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'absedieltechnologies@gmail.com')
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False
        )
        return True
    except Exception as e:
        logger.error(f"Fallback SMTP failed to send email to {to_email}: {e}")
        return False

@api_view(['POST'])
@throttle_classes([EmailRateThrottle])
def contact_submit(request):
    # If the payload came from quotation form (contains services list or timeline/budget)
    if 'timeline' in request.data or 'budget' in request.data or ('services' in request.data and isinstance(request.data['services'], list)):
        return quotation_submit(request)

    serializer = ContactSubmissionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Save submission
    try:
        submission = serializer.save()
    except Exception as e:
        logger.error(f"Error saving contact submission: {e}")
        return Response({'message': 'Failed to save contact submission to the database.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    name = submission.name
    email = submission.email
    phone = submission.phone
    service_interest = submission.service_interest
    message = submission.message

    # Admin Email (Requested format)
    admin_subject = f"New Contact Enquiry — {name}"
    admin_body = f"""NEW CONTACT ENQUIRY
Name: {name}
Email: {email}
Phone: {phone}
Service: {service_interest}
Message:
{message}
Submitted From:
ABSEDIEL Technologies Contact Page"""

    # User Confirmation Email
    user_subject = "Thank you for contacting ABSEDIEL Technologies"
    user_body = f"""Hi {name},

Thank you for getting in touch with us! We have received your inquiry regarding '{service_interest}'.
Our team will review your message and get back to you shortly.

Here is a summary of your inquiry:
- Service: {service_interest}
- Message: {message}

Best regards,
Team ABSEDIEL Technologies"""

    admin_recipient = getattr(settings, 'ADMIN_EMAIL', 'absedieltechnologies@gmail.com')
    email_sent_admin = send_email_notification(admin_recipient, admin_subject, admin_body)
    email_sent_user = send_email_notification(email, user_subject, user_body)
        
    return Response({
        'message': 'Thank you for getting in touch! We will get back to you shortly.',
        'submission_id': submission.id,
        'email_sent_user': email_sent_user,
        'email_sent_admin': email_sent_admin
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@throttle_classes([EmailRateThrottle])
def quotation_submit(request):
    data = request.data
    name = (data.get('name') or '').strip()
    company = (data.get('company') or '').strip()
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip()
    timeline = (data.get('timeline') or 'Within 1 Month').strip()
    budget = (data.get('budget') or '₹25,000 - ₹50,000').strip()
    description = (data.get('description') or data.get('message') or '').strip()

    services_raw = data.get('services') or data.get('serviceInterest') or []
    features_raw = data.get('features') or []

    # Validation
    if not name or not email or not phone or not description:
        return Response({
            'message': 'Please provide name, email, phone, and project description.'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Normalize services list & text
    if isinstance(services_raw, list):
        services_list = [str(s).strip() for s in services_raw if str(s).strip()]
    elif isinstance(services_raw, str):
        services_list = [s.strip() for s in services_raw.replace("\n", ",").split(",") if s.strip()]
    else:
        services_list = []

    if not services_list:
        services_list = ["Website Development"]

    services_db_str = ", ".join(services_list)
    services_email_text = "\n".join(f"✓ {s}" for s in services_list)

    # Service representation for Subject line
    if len(services_list) == 1:
        service_subject = services_list[0]
    elif len(services_list) == 2:
        service_subject = f"{services_list[0]}, {services_list[1]}"
    else:
        service_subject = f"{services_list[0]} & more"

    # Normalize features list & text
    if isinstance(features_raw, list):
        features_list = [str(f).strip() for f in features_raw if str(f).strip()]
    elif isinstance(features_raw, str) and features_raw.strip():
        features_list = [f.strip() for f in features_raw.replace("\n", ",").split(",") if f.strip()]
    else:
        features_list = []

    features_db_str = ", ".join(features_list) if features_list else ""
    features_email_text = "\n".join(f"✓ {f}" for f in features_list) if features_list else "None specified"

    company_display = company if company else "Individual / Not specified"

    # Save to QuotationSubmission
    submission = None
    try:
        submission = QuotationSubmission.objects.create(
            name=name,
            company=company,
            email=email,
            phone=phone,
            services=services_db_str,
            timeline=timeline,
            budget=budget,
            features=features_db_str,
            description=description
        )
    except Exception as e:
        logger.error(f"Error saving QuotationSubmission: {e}")
        # Fallback save to ContactSubmission
        try:
            ContactSubmission.objects.create(
                name=name,
                email=email,
                phone=phone[:50],
                service_interest=services_db_str[:255],
                message=f"Company: {company}\nTimeline: {timeline}\nBudget: {budget}\nFeatures: {features_db_str}\n\nRequirements:\n{description}"
            )
        except Exception as e2:
            logger.error(f"Fallback ContactSubmission save error: {e2}")

    # Admin Email (Requested format)
    admin_subject = f"NEW PROPOSAL REQUEST — {name} — {service_subject}"
    admin_body = f"""NEW CUSTOM PROPOSAL REQUEST

CONTACT DETAILS
----------------
Name: {name}
Company: {company_display}
Email: {email}
Phone / WhatsApp: {phone}


SERVICES REQUIRED
----------------
{services_email_text}


TIMELINE
----------------
{timeline}


ESTIMATED BUDGET
----------------
{budget}


TECHNICAL FEATURES
----------------
{features_email_text}


PROJECT REQUIREMENTS
----------------
{description}

Submitted From:
ABSEDIEL Technologies Proposal Request"""

    # User Confirmation Email
    user_subject = f"Proposal Request Received — ABSEDIEL Technologies"
    user_body = f"""Hi {name},

Thank you for requesting a project quotation and proposal from ABSEDIEL Technologies!

We have received your project details for {service_subject}.
Our technical architects and project leads will review your requirements and provide a comprehensive proposal within 24 hours.

Best regards,
Team ABSEDIEL Technologies
Website: https://absediel.com"""

    admin_recipient = getattr(settings, 'ADMIN_EMAIL', 'absedieltechnologies@gmail.com')
    email_sent_admin = send_email_notification(admin_recipient, admin_subject, admin_body)
    email_sent_user = send_email_notification(email, user_subject, user_body)

    return Response({
        'message': 'Thank you! Your quotation request has been received. Our team will review your requirements and send a customized proposal within 24 hours.',
        'submission_id': submission.id if submission else None,
        'email_sent_user': email_sent_user,
        'email_sent_admin': email_sent_admin
    }, status=status.HTTP_201_CREATED)
