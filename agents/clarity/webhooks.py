from agents.clarity.engine import ClarityEngine, PermissionRequired
from agents.clarity.models import InsightTheme
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Clarity."""
    engine = ClarityEngine()

    if event_type == 'feedback_received':
        # payload might have multiple responses, but let's assume it's an array of text
        responses = payload.get('responses', [])
        survey_name = payload.get('survey_name', 'General Feedback')

        if not responses:
            return

        try:
            themes = engine.extract_themes(responses, survey_name, instance=instance)
            for t in themes:
                # Add extracted themes
                theme_obj = InsightTheme.objects.create(
                    business=instance.business,
                    theme=t.get('theme', ''),
                    theme_type=t.get('theme_type', 'pain_point'),
                    mention_count=t.get('mention_count', 1),
                    priority_score=t.get('priority_score', 0),
                    example_quotes=t.get('example_quotes', [])
                )
                # Note: scoring might happen here or in the background task.
        except PermissionRequired as pr:
            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
