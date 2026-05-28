import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.nova.process_pending_queries")
def process_pending_queries():
    from agents.nova.models import DataQuery
    from agents.nova.engine import NovaEngine

    engine = NovaEngine()
    pending = DataQuery.objects.filter(status="pending")
    processed = 0

    for query in pending:
        try:
            result = engine.nl_to_sql(query)
            query.generated_sql = result.get("generated_sql", "")
            query.status = "completed"
            query.save(update_fields=["generated_sql", "status"])
            processed += 1
        except Exception as exc:
            logger.error("nova.process_pending_queries query %s: %s", query.pk, exc)
            query.status = "failed"
            query.save(update_fields=["status"])

    logger.info("nova.process_pending_queries: processed %d queries", processed)
    return processed


@shared_task(name="agents.nova.weekly_data_digest")
def weekly_data_digest():
    from agents.nova.models import DataQuery, DataSource
    from django.db.models import Count

    stats = {
        "queries_by_status": dict(DataQuery.objects.values_list("status").annotate(count=Count("id"))),
        "total_sources": DataSource.objects.filter(is_active=True).count(),
        "completed_this_week": DataQuery.objects.filter(status="completed").count(),
    }
    logger.info("nova.weekly_data_digest: %s", stats)
    return stats
