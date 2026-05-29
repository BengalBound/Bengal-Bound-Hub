from agents.scout.engine import ScoutEngine, PermissionRequired
from agents.scout.models import CompetitorChange, Competitor
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Scout."""
    engine = ScoutEngine()

    if event_type == 'competitor_intel':
        competitor, _ = Competitor.objects.get_or_create(
            business=instance.business,
            website=payload.get('competitor_url', ''),
            defaults={
                'name': payload.get('competitor_name', 'Unknown Competitor'),
            }
        )

        change = CompetitorChange.objects.create(
            business=instance.business,
            competitor=competitor,
            change_type=payload.get('change_type', 'other'),
            description=payload.get('description', ''),
            source_url=payload.get('source_url', ''),
        )

        try:
            res = engine.analyse_change(change, competitor, instance=instance)
            change.ai_analysis = res.get("ai_analysis", "")
            change.impact = res.get("impact_level", change.impact)
            change.save(update_fields=["ai_analysis", "impact"])
        except PermissionRequired as pr:
            if "res" in locals():
                change.ai_analysis = res.get("ai_analysis", "")
                change.impact = res.get("impact_level", change.impact)
                change.save(update_fields=["ai_analysis", "impact"])

            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
