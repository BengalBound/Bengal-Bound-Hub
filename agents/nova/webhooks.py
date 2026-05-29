from agents.nova.engine import NovaEngine, PermissionRequired
from agents.nova.models import DataQuery
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Nova."""
    engine = NovaEngine()

    if event_type == 'query_submitted':
        query = DataQuery.objects.create(
            business=instance.business,
            question=payload.get('question', ''),
            status='pending'
        )

        try:
            result = engine.nl_to_sql(query, instance=instance)
            query.generated_sql = result.get("generated_sql", "")
            query.status = "completed"
            query.save(update_fields=["generated_sql", "status"])
        except PermissionRequired as pr:
            if "result" in locals():
                query.generated_sql = result.get("generated_sql", "")

            query.status = "failed"
            query.save(update_fields=["generated_sql", "status"])

            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
