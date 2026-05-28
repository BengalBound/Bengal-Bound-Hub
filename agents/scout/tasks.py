import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.scout.analyse_unprocessed_changes")
def analyse_unprocessed_changes():
    from agents.scout.models import CompetitorChange, Competitor
    from agents.scout.engine import ScoutEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='scout')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = ScoutEngine()
    processed = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        unanalysed = CompetitorChange.objects.filter(business=instance.business, ai_analysis="").select_related("competitor")
        for change in unanalysed:
            try:
                result = engine.analyse_change(change, change.competitor, instance=instance)
                change.ai_analysis = result.get("ai_analysis", "")
                change.impact = result.get("impact_level", change.impact)
                change.save(update_fields=["ai_analysis", "impact"])
                processed += 1

                if result.get("urgency") == "act_now":
                    logger.warning("Scout URGENT: %s change by %s requires immediate response",
                                   change.change_type, change.competitor.name)
            except PermissionRequired as pr:
                # Save partial state
                if "result" in locals():
                    change.ai_analysis = locals()['result'].get("ai_analysis", "")
                    change.impact = locals()['result'].get("impact_level", change.impact)
                    change.save(update_fields=["ai_analysis", "impact"])
                
                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
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
    from agents.models import AgentInstance, AgentCatalog

    try:
        catalog = AgentCatalog.objects.get(slug='scout')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = ScoutEngine()
    week_ago = timezone.now() - timedelta(days=7)
    processed = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        business = instance.business
        competitors = list(Competitor.objects.filter(business=business, is_active=True))
        if not competitors:
            continue
        changes = list(CompetitorChange.objects.filter(
            business=business, detected_at__gte=week_ago
        ).select_related("competitor"))
        try:
            summary = engine.weekly_intel_summary(changes, competitors, instance=instance)
            logger.info("Scout weekly digest for %s: generated", business.slug)
            processed += 1
        except Exception as exc:
            logger.error("scout.weekly_intel_digest business %s: %s", business.slug, exc)

    logger.info("scout.weekly_intel_digest: processed %d businesses", processed)
    return processed
