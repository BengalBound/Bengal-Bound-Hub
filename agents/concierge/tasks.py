import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.concierge.process_unclassified_emails")
def process_unclassified_emails():
    from agents.concierge.models import EmailTriage
    from agents.concierge.engine import ConciergeEngine

    engine = ConciergeEngine()
    unprocessed = EmailTriage.objects.filter(is_processed=False)
    classified = 0

    for email in unprocessed:
        try:
            result = engine.triage_email(email)
            email.category = result.get("category", email.category)
            email.priority = result.get("priority", email.priority)
            email.is_processed = True
            email.save(update_fields=["category", "priority", "is_processed"])
            classified += 1
        except Exception as exc:
            logger.error("concierge.process_unclassified_emails email %s: %s", email.pk, exc)

    logger.info("concierge.process_unclassified_emails: classified %d emails", classified)
    return classified


@shared_task(name="agents.concierge.follow_up_pending_meetings")
def follow_up_pending_meetings():
    from django.utils import timezone
    from datetime import timedelta
    from agents.concierge.models import MeetingRequest

    cutoff = timezone.now() - timedelta(hours=24)
    stale = MeetingRequest.objects.filter(status="pending", created_at__lt=cutoff)
    count = stale.count()
    logger.warning("concierge: %d meeting requests pending >24h, need follow-up", count)
    return count


@shared_task(name="agents.concierge.daily_inbox_digest")
def daily_inbox_digest():
    from agents.concierge.models import EmailTriage
    from django.db.models import Count

    stats = (EmailTriage.objects
             .values("business_id", "category", "priority")
             .annotate(count=Count("id")))
    logger.info("concierge.daily_inbox_digest: %d stat rows", len(stats))
    return list(stats)
