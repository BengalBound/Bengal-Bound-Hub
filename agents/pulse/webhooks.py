from agents.pulse.engine import PulseEngine, PermissionRequired
from agents.pulse.models import ResearchConfig, ResearchReport
from agents.models import AgentInstance, AgentPermissionRequest
from django.utils import timezone

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Pulse."""
    engine = PulseEngine()

    if event_type == 'report_requested':
        config = ResearchConfig.objects.filter(business=instance.business).first()
        if not config:
            config = ResearchConfig.objects.create(
                business=instance.business,
                industry=payload.get('industry', 'General')
            )

        period = timezone.now().strftime("%Y-W%U")
        report = ResearchReport.objects.create(
            business=instance.business,
            period=period
        )

        try:
            result = engine.generate_report(config, report, instance=instance)
            report.narrative = result.get("narrative", "")
            report.key_findings = result.get("key_findings", [])
            report.opportunities = result.get("opportunities", [])
            report.threats = result.get("threats", [])
            report.recommendations = result.get("recommendations", [])
            report.save()
        except PermissionRequired as pr:
            if "result" in locals():
                report.narrative = result.get("narrative", "")
                report.save(update_fields=["narrative"])
            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
