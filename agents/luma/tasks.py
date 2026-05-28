import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.luma.scan_unanalysed_mentions")
def scan_unanalysed_mentions():
    from agents.luma.models import BrandMention
    from agents.luma.engine import LumaEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='luma')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = LumaEngine()
    processed = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        unanalysed = BrandMention.objects.filter(business=instance.business, ai_summary="")
        for mention in unanalysed:
            try:
                result = engine.analyse_mention(mention, instance=instance)
                mention.sentiment = result.get("sentiment", mention.sentiment)
                mention.urgency = result.get("urgency", mention.urgency)
                mention.ai_summary = result.get("ai_summary", "")
                mention.save(update_fields=["sentiment", "urgency", "ai_summary"])
                processed += 1
            except PermissionRequired as pr:
                # We save what we have first
                if "sentiment" in locals().get('result', {}):
                    mention.sentiment = locals()['result'].get("sentiment", mention.sentiment)
                    mention.urgency = locals()['result'].get("urgency", mention.urgency)
                    mention.ai_summary = locals()['result'].get("ai_summary", "")
                    mention.save(update_fields=["sentiment", "urgency", "ai_summary"])

                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("luma.scan_unanalysed_mentions mention %s: %s", mention.pk, exc)

    logger.info("luma.scan_unanalysed_mentions: processed %d mentions", processed)
    return processed


@shared_task(name="agents.luma.crisis_alert_check")
def crisis_alert_check():
    from agents.luma.models import BrandMention

    crisis_mentions = BrandMention.objects.filter(urgency="crisis", responded=False)
    count = crisis_mentions.count()
    if count:
        logger.critical("LUMA: %d unresponded CRISIS mentions — immediate action required!", count)
    return count


@shared_task(name="agents.luma.weekly_brand_digest")
def weekly_brand_digest():
    from agents.luma.models import BrandMention
    from django.db.models import Count

    stats = dict(BrandMention.objects.values_list("sentiment").annotate(count=Count("id")))
    logger.info("luma.weekly_brand_digest: sentiment distribution %s", stats)
    return stats
