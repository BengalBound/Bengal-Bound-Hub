from agents.hera.engine import HeraEngine, PermissionRequired
from agents.hera.models import PolicyQuery
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Hera."""
    engine = HeraEngine()

    if event_type == 'policy_query':
        query = PolicyQuery.objects.create(
            business=instance.business,
            employee_name=payload.get('employee_name', 'Unknown'),
            question=payload.get('question', ''),
            category=payload.get('category', 'general'),
            ai_answer=""
        )

        try:
            query.ai_answer = engine.answer_policy_query(query, instance=instance)
            query.save(update_fields=["ai_answer"])
        except PermissionRequired as pr:
            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
