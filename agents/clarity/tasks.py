import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.clarity.weekly_insight_digest")
def weekly_insight_digest():
    from agents.clarity.models import InsightTheme
    from agents.clarity.engine import ClarityEngine
    from hub.models import BusinessInstance
    from django.utils import timezone

    engine = ClarityEngine()
    period = timezone.now().strftime("%Y-W%U")
    processed = 0

    for business in BusinessInstance.objects.filter(is_active=True):
        themes = list(InsightTheme.objects.filter(business=business).order_by("-priority_score")[:15])
        if not themes:
            continue
        try:
            report = engine.weekly_insight_report(themes, period)
            logger.info("Clarity weekly digest for %s: generated", business.slug)
            processed += 1
        except Exception as exc:
            logger.error("clarity.weekly_insight_digest business %s: %s", business.slug, exc)

    logger.info("clarity.weekly_insight_digest: processed %d businesses", processed)
    return processed


@shared_task(name="agents.clarity.auto_score_themes")
def auto_score_themes():
    from agents.clarity.models import InsightTheme
    from agents.clarity.engine import ClarityEngine

    engine = ClarityEngine()
    unscored = InsightTheme.objects.filter(priority_score=0)
    updated = 0

    for theme in unscored:
        try:
            result = engine.analyse_theme(theme)
            theme.ai_analysis = result.get("analysis", "")
            theme.save(update_fields=["ai_analysis"])
            updated += 1
        except Exception as exc:
            logger.error("clarity.auto_score_themes theme %s: %s", theme.pk, exc)

    logger.info("clarity.auto_score_themes: updated %d themes", updated)
    return updated
