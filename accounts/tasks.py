import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from accounts.models import User
from bengalbound_core.notifications import send_system_email

logger = logging.getLogger(__name__)

@shared_task
def process_daily_onboarding_emails():
    """
    Runs daily to evaluate user tenure and send drip campaign emails.
    """
    now = timezone.now()
    
    # We define the days and the corresponding email templates/subjects
    drip_schedule = {
        1: {
            'subject': 'Welcome to BengalBound & First Steps',
            'template': 'emails/onboarding_day1.html'
        },
        3: {
            'subject': 'Meet your AI Assistants',
            'template': 'emails/onboarding_day3.html'
        },
        7: {
            'subject': 'How to invite your team',
            'template': 'emails/onboarding_day7.html'
        },
        30: {
            'subject': 'Checking in: Your first month review',
            'template': 'emails/onboarding_day30.html'
        }
    }
    
    # In a production system we would track if an email was already sent via a model,
    # but for simplicity we'll just check if their date_joined matches exactly X days ago.
    
    for days, details in drip_schedule.items():
        # Find users who joined exactly `days` ago (between start and end of that day)
        target_date = now - timedelta(days=days)
        
        users_to_email = User.objects.filter(
            date_joined__date=target_date.date(),
            is_active=True
        )
        
        for user in users_to_email:
            # We can pass context here
            context = {
                'user': user,
                'name': user.get_full_name() or user.username,
            }
            send_system_email(user, details['subject'], details['template'], context)
            logger.info(f"Sent Day {days} onboarding email to {user.email}")
