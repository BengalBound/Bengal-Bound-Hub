import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.oracle.weekly_seo_audit")
def weekly_seo_audit():
    from django.utils import timezone
    from agents.oracle.models import Website, SEOIssue
    from agents.oracle.engine import OracleEngine

    engine = OracleEngine()
    websites = Website.objects.all()
    issues_created = 0

    for website in websites:
        try:
            issues = engine.audit_website(website)
            for issue_data in issues:
                SEOIssue.objects.get_or_create(
                    business=website.business,
                    website=website,
                    issue_type=issue_data.get("issue_type", "missing_meta"),
                    page_url=issue_data.get("page_url", website.domain),
                    defaults={
                        "severity": issue_data.get("severity", "info"),
                        "description": issue_data.get("description", ""),
                        "fix_suggestion": issue_data.get("fix_suggestion", ""),
                    },
                )
                issues_created += 1
            website.last_crawled = timezone.now()
            website.save(update_fields=["last_crawled"])
        except Exception as exc:
            logger.error("oracle.weekly_seo_audit website %s: %s", website.pk, exc)

    logger.info("oracle.weekly_seo_audit: created %d issue records", issues_created)
    return issues_created


@shared_task(name="agents.oracle.auto_generate_fixes")
def auto_generate_fixes():
    from agents.oracle.models import SEOIssue
    from agents.oracle.engine import OracleEngine

    engine = OracleEngine()
    open_issues = SEOIssue.objects.filter(status="open", fix_suggestion="", severity__in=["critical", "warning"])
    fixed = 0

    for issue in open_issues:
        try:
            issue.fix_suggestion = engine.generate_fix(issue)
            issue.save(update_fields=["fix_suggestion"])
            fixed += 1
        except Exception as exc:
            logger.error("oracle.auto_generate_fixes issue %s: %s", issue.pk, exc)

    logger.info("oracle.auto_generate_fixes: generated %d fixes", fixed)
    return fixed
