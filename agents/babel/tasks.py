import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.babel.process_queued_jobs")
def process_queued_jobs():
    from agents.babel.models import TranslationJob, TranslationOutput
    from agents.babel.engine import BabelEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='babel')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = BabelEngine()
    completed = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        queued = TranslationJob.objects.filter(business=instance.business, status="queued")
        for job in queued:
            try:
                job.status = "processing"
                job.save(update_fields=["status"])

                results = engine.translate(job, instance=instance)
                for result in results:
                    TranslationOutput.objects.update_or_create(
                        job=job,
                        target_language=result["language"],
                        defaults={
                            "translated_text": result.get("translated_text", ""),
                            "quality_score": result.get("quality_score", 0.7),
                        },
                    )

                job.status = "completed"
                job.save(update_fields=["status"])
                completed += 1
            except PermissionRequired as pr:
                if "results" in locals():
                    for result in results:
                        TranslationOutput.objects.update_or_create(
                            job=job, target_language=result["language"],
                            defaults={"translated_text": result.get("translated_text", ""), "quality_score": result.get("quality_score", 0.7)}
                        )
                job.status = "failed"
                job.save(update_fields=["status"])
                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("babel.process_queued_jobs job %s: %s", job.pk, exc)
                job.status = "failed"
                job.save(update_fields=["status"])

    logger.info("babel.process_queued_jobs: completed %d jobs", completed)
    return completed


@shared_task(name="agents.babel.retry_failed_jobs")
def retry_failed_jobs():
    from agents.babel.models import TranslationJob

    count = TranslationJob.objects.filter(status="failed").update(status="queued")
    logger.info("babel.retry_failed_jobs: re-queued %d jobs", count)
    return count
