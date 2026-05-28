import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.video_concierge.daily_session_digest")
def daily_session_digest():
    from django.utils import timezone
    from datetime import timedelta
    from agents.video_concierge.models import VideoSession
    from django.db.models import Count

    yesterday = timezone.now() - timedelta(days=1)
    stats = (
        VideoSession.objects.filter(started_at__gte=yesterday)
        .values('organization_id', 'session_type', 'resolution_status')
        .annotate(count=Count('id'))
    )
    logger.info("video_concierge.daily_session_digest: %s", list(stats))
    return list(stats)
