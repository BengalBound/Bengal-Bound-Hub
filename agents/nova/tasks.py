import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.nova.process_pending_queries")
def process_pending_queries():
    from agents.nova.models import DataQuery
    from agents.nova.engine import NovaEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='nova')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = NovaEngine()
    processed = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        pending = DataQuery.objects.filter(business=instance.business, status="pending")
        for query in pending:
            try:
                result = engine.nl_to_sql(query, instance=instance)
                query.generated_sql = result.get("generated_sql", "")
                query.status = "completed"
                query.save(update_fields=["generated_sql", "status"])
                processed += 1
            except PermissionRequired as pr:
                # Save what we have and pause
                query.generated_sql = locals()['result'].get("generated_sql", "") if "result" in locals() else ""
                query.status = "failed" # Mark failed so it doesn't run automatically
                query.save(update_fields=["generated_sql", "status"])

                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
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
