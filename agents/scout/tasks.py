import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.scout.analyse_unprocessed_changes")
def analyse_unprocessed_changes():
    from agents.scout.models import CompetitorChange, Competitor
    from agents.scout.engine import ScoutEngine

    engine = ScoutEngine()
    unanalysed = CompetitorChange.objects.filter(ai_analysis="").select_related("competitor")
    processed = 0

    for change in unanalysed:
        try:
            result = engine.analyse_change(change, change.competitor)
            change.ai_analysis = result.get("ai_analysis", "")
            change.impact = result.get("impact_level", change.impact)
            change.save(update_fields=["ai_analysis", "impact"])
            processed += 1

            if result.get("urgency") == "act_now":
                logger.warning("Scout URGENT: %s change by %s requires immediate response",
                               change.change_type, change.competitor.name)
        except Exception as exc:
            logger.error("scout.analyse_unprocessed_changes change %s: %s", change.pk, exc)

    logger.info("scout.analyse_unprocessed_changes: processed %d changes", processed)
    return processed


@shared_task(name="agents.scout.weekly_intel_digest")
def weekly_intel_digest():
    from django.utils import timezone
    from datetime import timedelta
    from agents.scout.models import CompetitorChange, Competitor
    from agents.scout.engine import ScoutEngine
    from hub.models import BusinessInstance

    engine = ScoutEngine()
    week_ago = timezone.now() - timedelta(days=7)
    processed = 0

    for business in BusinessInstance.objects.filter(is_active=True):
        competitors = list(Competitor.objects.filter(business=business, is_active=True))
        if not competitors:
            continue
        changes = list(CompetitorChange.objects.filter(
            business=business, detected_at__gte=week_ago
        ).select_related("competitor"))
        try:
            summary = engine.weekly_intel_summary(changes, competitors)
            logger.info("Scout weekly digest for %s: generated", business.slug)
            processed += 1
        except Exception as exc:
            logger.error("scout.weekly_intel_digest business %s: %s", business.slug, exc)

    logger.info("scout.weekly_intel_digest: processed %d businesses", processed)
    return processed
