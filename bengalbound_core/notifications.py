import logging
import requests
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

try:
    import firebase_admin
    from firebase_admin import messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

logger = logging.getLogger(__name__)

def send_slack_alert(title: str, message: str, urgency: str = 'normal'):
    """
    Sends an alert to the internal Slack operations channel.
    Urgency: 'normal', 'high', 'critical'
    """
    webhook_url = getattr(settings, 'SLACK_INTERNAL_WEBHOOK_URL', None)
    if not webhook_url:
        logger.warning(f"Slack alert suppressed (no webhook URL configured): {title} - {message}")
        return False

    emoji = {
        'normal': ':information_source:',
        'high': ':warning:',
        'critical': ':rotating_light:'
    }.get(urgency, ':information_source:')

    payload = {
        "text": f"{emoji} *{title}*\n{message}"
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {str(e)}")
        return False

def send_fcm_push(user, title: str, body: str, data: dict = None):
    """
    Sends a push notification to the user's registered device.
    """
    if not FIREBASE_AVAILABLE:
        logger.warning("FCM Push failed: firebase_admin not installed")
        return False
        
    if not user.fcm_token:
        logger.info(f"FCM Push skipped: No FCM token for user {user.email}")
        return False

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=user.fcm_token,
        )
        response = messaging.send(message)
        logger.info(f"Successfully sent message to {user.email}: {response}")
        return True
    except Exception as e:
        logger.error(f"Failed to send FCM push to {user.email}: {str(e)}")
        return False

def send_system_email(user, subject: str, template_name: str, context: dict):
    """
    Sends a templated email to the user.
    """
    try:
        # Default to base context if needed
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send email {subject} to {user.email}: {str(e)}")
        return False
