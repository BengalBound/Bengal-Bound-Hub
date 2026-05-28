import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.lead_hunter.score_new_prospects")
def score_new_prospects():
    from agents.lead_hunter.models import Prospect
    from agents.lead_hunter.engine import LeadHunterEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='lead_hunter')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = LeadHunterEngine()
    processed = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        unscored = Prospect.objects.filter(business=instance.business, score=0, status="new")
        for prospect in unscored:
            try:
                result = engine.score_prospect(prospect, instance=instance)
                prospect.score = result.get("score", 50)
                prospect.ai_summary = result.get("ai_summary", "")
                prospect.save(update_fields=["score", "ai_summary"])
                processed += 1
            except PermissionRequired as pr:
                # Save partial data if possible
                if "result" in locals():
                    prospect.score = locals()['result'].get("score", 50)
                    prospect.ai_summary = locals()['result'].get("ai_summary", "")
                    prospect.save(update_fields=["score", "ai_summary"])

                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("lead_hunter.score_new_prospects prospect %s: %s", prospect.pk, exc)

    logger.info("lead_hunter.score_new_prospects: scored %d prospects", processed)
    return processed


@shared_task(name="agents.lead_hunter.activate_ready_sequences")
def activate_ready_sequences():
    from agents.lead_hunter.models import OutreachSequence

    draft_with_prospects = OutreachSequence.objects.filter(
        status="draft",
    ).prefetch_related("prospects")

    activated = 0
    for seq in draft_with_prospects:
        if seq.prospects.filter(score__gte=60).exists():
            seq.status = "active"
            seq.save(update_fields=["status"])
            activated += 1
            logger.info("lead_hunter: activated sequence [%s]", seq.name)

    logger.info("lead_hunter.activate_ready_sequences: activated %d sequences", activated)
    return activated


@shared_task(name="agents.lead_hunter.weekly_pipeline_digest")
def weekly_pipeline_digest():
    from agents.lead_hunter.models import Prospect
    from django.db.models import Count, Avg

    stats = {
        "by_status": dict(Prospect.objects.values_list("status").annotate(count=Count("id"))),
        "avg_score": Prospect.objects.aggregate(avg=Avg("score"))["avg"] or 0,
        "high_priority": Prospect.objects.filter(score__gte=70).count(),
    }
    logger.info("lead_hunter.weekly_pipeline_digest: %s", stats)
    return stats
