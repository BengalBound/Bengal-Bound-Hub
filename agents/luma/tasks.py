import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.luma.scan_unanalysed_mentions")
def scan_unanalysed_mentions():
    from agents.luma.models import BrandMention
    from agents.luma.engine import LumaEngine

    engine = LumaEngine()
    unanalysed = BrandMention.objects.filter(ai_summary="")
    processed = 0

    for mention in unanalysed:
        try:
            result = engine.analyse_mention(mention)
            mention.sentiment = result.get("sentiment", mention.sentiment)
            mention.urgency = result.get("urgency", mention.urgency)
            mention.ai_summary = result.get("ai_summary", "")
            mention.save(update_fields=["sentiment", "urgency", "ai_summary"])
            processed += 1

            if result.get("urgency") == "crisis":
                logger.critical("LUMA CRISIS ALERT: %s — %s", mention.source, mention.title)
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
