from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from agents.models import AgentPermissionRequest
from .base import BaseAgentAdapter

class EmailAdapter(BaseAgentAdapter):
    def send_notification(self, subject: str, body: str, to_emails: list) -> bool:
        try:
            send_mail(
                subject,
                body,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bengalbound.com'),
                to_emails,
                fail_silently=False,
            )
            return True
        except Exception as e:
            return False

    def send_permission_request(self, request: AgentPermissionRequest, to_emails: list) -> bool:
        subject = f"[{self.instance.catalog.name}] Permission Required"
        
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        url = site_url + reverse('agent_permission_respond', args=[request.pk])
        
        body = f"""
Agent {self.instance.catalog.name} requires your permission.

Context: {request.context}
Option A: {request.option_a}
Option B: {request.option_b}

Please respond here: {url}
"""
        return self.send_notification(subject, body, to_emails)
