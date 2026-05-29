from agents.kai.engine import KaiEngine, PermissionRequired
from agents.kai.models import Incident, Pipeline
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Kai."""
    engine = KaiEngine()

    if event_type == 'incident':
        incident, _ = Incident.objects.get_or_create(
            business=instance.business,
            incident_id=payload.get('id', ''),
            defaults={
                'title': payload.get('title', 'Unknown Incident'),
                'description': payload.get('description', ''),
                'severity': payload.get('severity', 'medium'),
                'status': 'open'
            }
        )
        try:
            res = engine.analyze_incident(incident, instance=instance)
            incident.ai_root_cause = res.get("root_cause", "")
            incident.status = "investigating"
            incident.save(update_fields=["ai_root_cause", "status"])
        except PermissionRequired as pr:
            AgentPermissionRequest.objects.create(
                instance=instance,
                context=pr.context,
                option_a=pr.option_a,
                option_b=pr.option_b,
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])

    elif event_type == 'pipeline_fail':
        pipeline, _ = Pipeline.objects.get_or_create(
            business=instance.business,
            name=payload.get('pipeline_name', 'Unknown Pipeline'),
            defaults={
                'provider': payload.get('provider', 'github'),
                'repo_url': payload.get('repo_url', ''),
            }
        )
        pipeline.last_status = 'failing'
        pipeline.save(update_fields=['last_status'])

        try:
            engine.pipeline_health_check(pipeline, instance=instance)
        except PermissionRequired as pr:
            AgentPermissionRequest.objects.create(
                instance=instance,
                context=pr.context,
                option_a=pr.option_a,
                option_b=pr.option_b,
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
