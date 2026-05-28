import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.clarity.weekly_insight_digest")
def weekly_insight_digest():
    from agents.clarity.models import InsightTheme
    from agents.clarity.engine import ClarityEngine
    from agents.models import AgentInstance, AgentCatalog
    from django.utils import timezone

    try:
        catalog = AgentCatalog.objects.get(slug='clarity')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = ClarityEngine()
    period = timezone.now().strftime("%Y-W%U")
    processed = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        themes = list(InsightTheme.objects.filter(business=instance.business).order_by("-priority_score")[:15])
        if not themes:
            continue
        try:
            report = engine.weekly_insight_report(themes, period, instance=instance)
            logger.info("Clarity weekly digest for %s: generated", instance.business.slug)
            processed += 1
        except Exception as exc:
            logger.error("clarity.weekly_insight_digest instance %s: %s", instance.pk, exc)

    logger.info("clarity.weekly_insight_digest: processed %d instances", processed)
    return processed


@shared_task(name="agents.clarity.auto_score_themes")
def auto_score_themes():
    from agents.clarity.models import InsightTheme
    from agents.clarity.engine import ClarityEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='clarity')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = ClarityEngine()
    updated = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        unscored = InsightTheme.objects.filter(business=instance.business, priority_score=0)
        for theme in unscored:
            try:
                result = engine.analyse_theme(theme, instance=instance)
                theme.ai_analysis = result.get("analysis", "")
                theme.save(update_fields=["ai_analysis"])
                updated += 1
            except PermissionRequired as pr:
                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("clarity.auto_score_themes theme %s: %s", theme.pk, exc)

    logger.info("clarity.auto_score_themes: updated %d themes", updated)
    return updated
