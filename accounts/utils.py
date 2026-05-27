import random
import string
from django.core.mail import send_mail
from django.conf import settings

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(user, otp):
    subject = 'Your BengalBound Verification Code'
    message = f'Hello! Your One-Time Password (OTP) for verifying your BengalBound account is {otp}.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
