import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.serea_content.auto_generate_draft_pieces")
def auto_generate_draft_pieces():
    from agents.serea_content.models import ContentPiece
    from agents.serea_content.engine import SereaContentEngine
    from agents.models import AgentInstance, AgentCatalog

    try:
        catalog = AgentCatalog.objects.get(slug='serea_content')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = SereaContentEngine()
    generated = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        drafts = ContentPiece.objects.filter(campaign__business=instance.business, status="draft", generated_content="")
        for piece in drafts:
            try:
                content = engine.generate_piece(piece, instance=instance)
                piece.generated_content = content
                piece.word_count = len(content.split())
                piece.status = "generated"
                piece.save(update_fields=["generated_content", "word_count", "status"])
                generated += 1
            except Exception as exc:
                logger.error("serea_content.auto_generate_draft_pieces piece %s: %s", piece.pk, exc)

    logger.info("serea_content.auto_generate_draft_pieces: generated %d pieces", generated)
    return generated


@shared_task(name="agents.serea_content.campaign_strategy_generation")
def campaign_strategy_generation():
    from agents.serea_content.models import Campaign
    from agents.serea_content.engine import SereaContentEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='serea_content')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = SereaContentEngine()
    processed = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        active = Campaign.objects.filter(business=instance.business, status="active")
        for campaign in active:
            pieces_count = campaign.content_pieces.count()
            if pieces_count == 0:
                try:
                    strategy = engine.campaign_strategy(campaign, instance=instance)
                    logger.info("serea_content: campaign '%s' strategy generated — suggested mix: %s",
                                campaign.name, strategy.get("content_mix", {}))
                    processed += 1
                except PermissionRequired as pr:
                    AgentPermissionRequest.objects.create(
                        instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                    )
                    instance.status = 'waiting'
                    instance.save(update_fields=['status'])
                except Exception as exc:
                    logger.error("serea_content.campaign_strategy_generation campaign %s: %s", campaign.pk, exc)

    logger.info("serea_content.campaign_strategy_generation: processed %d campaigns", processed)
    return processed


@shared_task(name="agents.serea_content.weekly_content_digest")
def weekly_content_digest():
    from agents.serea_content.models import ContentPiece
    from django.db.models import Count

    stats = dict(ContentPiece.objects.values_list("status").annotate(count=Count("id")))
    logger.info("serea_content.weekly_content_digest: %s", stats)
    return stats
