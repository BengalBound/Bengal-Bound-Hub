import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.serea_content.auto_generate_draft_pieces")
def auto_generate_draft_pieces():
    from agents.serea_content.models import ContentPiece
    from agents.serea_content.engine import SereaContentEngine

    engine = SereaContentEngine()
    drafts = ContentPiece.objects.filter(status="draft", generated_content="")
    generated = 0

    for piece in drafts:
        try:
            content = engine.generate_piece(piece)
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
    from agents.serea_content.engine import SereaContentEngine

    engine = SereaContentEngine()
    active = Campaign.objects.filter(status="active")
    processed = 0

    for campaign in active:
        pieces_count = campaign.content_pieces.count()
        if pieces_count == 0:
            try:
                strategy = engine.campaign_strategy(campaign)
                logger.info("serea_content: campaign '%s' strategy generated — suggested mix: %s",
                            campaign.name, strategy.get("content_mix", {}))
                processed += 1
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
