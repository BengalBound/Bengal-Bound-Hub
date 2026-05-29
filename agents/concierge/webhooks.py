from agents.concierge.engine import ConciergeEngine, PermissionRequired
from agents.concierge.models import EmailTriage
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Concierge."""
    engine = ConciergeEngine()

    if event_type == 'email_received':
        email = EmailTriage.objects.create(
            business_id=instance.business.id,
            sender=payload.get('sender', ''),
            subject=payload.get('subject', ''),
            body_preview=payload.get('body_preview', ''),
            is_processed=False
        )

        try:
            # Triage immediately
            result = engine.triage_email(email, instance=instance)
            email.category = result.get("category", email.category)
            email.priority = result.get("priority", email.priority)
            email.is_processed = True
            email.save(update_fields=["category", "priority", "is_processed"])
        except PermissionRequired as pr:
            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
