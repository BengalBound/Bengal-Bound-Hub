from django.utils import timezone
from agents.oracle.engine import OracleEngine, PermissionRequired
from agents.oracle.models import Website, SEOIssue
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Oracle."""
    engine = OracleEngine()

    if event_type == 'website_crawled':
        website, _ = Website.objects.get_or_create(
            business=instance.business,
            domain=payload.get('domain', ''),
            defaults={
                'cms': payload.get('cms', 'Unknown'),
            }
        )

        try:
            issues = engine.audit_website(website, instance=instance)
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
            website.last_crawled = timezone.now()
            website.save(update_fields=["last_crawled"])
        except PermissionRequired as pr:
            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
