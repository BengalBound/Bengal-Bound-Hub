from agents.luma.engine import LumaEngine, PermissionRequired
from agents.luma.models import BrandMention
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Luma."""
    engine = LumaEngine()

    if event_type == 'mention_detected':
        mention, _ = BrandMention.objects.get_or_create(
            business=instance.business,
            url=payload.get('url', ''),
            defaults={
                'source': payload.get('source', 'Web'),
                'title': payload.get('title', 'Unknown Title'),
                'snippet': payload.get('snippet', ''),
            }
        )

        try:
            res = engine.analyse_mention(mention, instance=instance)
            mention.sentiment = res.get("sentiment", mention.sentiment)
            mention.urgency = res.get("urgency", mention.urgency)
            mention.ai_summary = res.get("ai_summary", "")
            mention.save(update_fields=["sentiment", "urgency", "ai_summary"])
        except PermissionRequired as pr:
            if "sentiment" in locals().get('res', {}):
                mention.sentiment = res.get("sentiment", mention.sentiment)
                mention.urgency = res.get("urgency", mention.urgency)
                mention.ai_summary = res.get("ai_summary", "")
                mention.save(update_fields=["sentiment", "urgency", "ai_summary"])

            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
