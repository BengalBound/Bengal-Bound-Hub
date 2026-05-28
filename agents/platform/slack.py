import json
import logging
import requests

from .base import BaseAgentAdapter

logger = logging.getLogger(__name__)


class SlackAdapter(BaseAgentAdapter):
    """Post messages and alerts to a Slack Incoming Webhook."""

    def _webhook_url(self) -> str:
        from agents.models import AgentIntegration
        integration = AgentIntegration.objects.filter(
            instance=self.instance, platform='slack', status='connected'
        ).first()
        if not integration:
            raise ValueError(f"No Slack integration configured for instance {self.instance.pk}")
        return integration.credential  # decrypted by EncryptedTextField

    def send_notification(self, title: str, message: str, urgency: str = 'normal') -> bool:
        emoji = {'normal': ':robot_face:', 'high': ':warning:', 'critical': ':rotating_light:'}.get(urgency, ':robot_face:')
        payload = {
            "text": f"{emoji} *{title}*\n{message}",
            "username": self.instance.catalog.name,
        }
        return self._post(payload)

    def send_alert(self, title: str, detail: str, color: str = '#36a64f') -> bool:
        payload = {
            "username": self.instance.catalog.name,
            "attachments": [{"color": color, "title": title, "text": detail, "mrkdwn_in": ["text"]}],
        }
        return self._post(payload)

    def send_permission_request(self, request, to_emails: list = None) -> bool:
        from django.conf import settings
        from django.urls import reverse
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:1234')
        url = site_url + reverse('agent_permission_respond', args=[request.pk])
        payload = {
            "username": self.instance.catalog.name,
            "text": (
                f":pause_button: *Permission Required — {self.instance.catalog.name}*\n"
                f"*Context:* {request.context}\n"
                f"*Option A:* {request.option_a}\n"
                f"*Option B:* {request.option_b or 'N/A'}\n"
                f"<{url}|Respond here>"
            ),
        }
        return self._post(payload)

    def push_event(self, event_type: str, payload: dict) -> bool:
        return self.send_notification(event_type, json.dumps(payload, indent=2))

    def test_connection(self) -> bool:
        return self.send_notification("BengalBound Agent", "Connection test successful.")

    def _post(self, payload: dict) -> bool:
        try:
            url = self._webhook_url()
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            return True
        except Exception as exc:
            logger.error("SlackAdapter._post failed for instance %s: %s", self.instance.pk, exc)
            return False
