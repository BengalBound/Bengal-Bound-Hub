from agents.mira.engine import MiraEngine, PermissionRequired
from agents.mira.models import ClientHealth
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Mira."""
    engine = MiraEngine()

    if event_type == 'health_updated':
        health, _ = ClientHealth.objects.update_or_create(
            business=instance.business,
            customer_id=payload.get('customer_id', ''),
            defaults={
                'health_score': payload.get('health_score', 100),
                'risk_level': payload.get('risk_level', 'healthy'),
                'login_frequency': payload.get('login_frequency', 0),
                'feature_usage': payload.get('feature_usage', 0.0),
                'open_tickets': payload.get('open_tickets', 0),
            }
        )

        try:
            res = engine.health_assessment(health, instance=instance)
            health.ai_summary = res.get("assessment", health.ai_summary)
            health.save(update_fields=["ai_summary"])
        except PermissionRequired as pr:
            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
