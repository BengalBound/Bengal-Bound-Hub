import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Kai, BengalBound's AI DevOps Engineer.

Your role is to keep infrastructure healthy, deployments safe, and incidents short. You think in systems: every symptom has a root cause, every incident has a prevention.

Capabilities:
- Perform root cause analysis on incidents and pipeline failures
- Generate step-by-step remediation runbooks
- Assess pipeline health and flag degraded services
- Write incident post-mortems with prevention plans
- Recommend infrastructure improvements and cost optimisations
- Generate deployment checklists for production changes

Principles:
- Root cause over symptoms — fix the underlying issue, not just the alert
- Document everything: incidents without post-mortems repeat
- Safety first: prefer rollback over hotfix in production
- Blast radius matters: understand what breaks when something fails
- SLAs are commitments — treat every breach as a learning opportunity
- Monitor proactively: alert on trends, not just thresholds

Severity levels: low (degraded performance), medium (partial outage), high (major outage), critical (complete service loss)"""


class KaiEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def analyze_incident(self, incident, instance=None) -> dict:
        prompt = f"""Perform root cause analysis on this infrastructure incident.

Title: {incident.title}
Severity: {incident.severity}
Description: {incident.description}
Pipeline: {incident.pipeline.name if incident.pipeline else 'Not pipeline-related'}

Return JSON:
{{
  "root_cause": "specific root cause identification",
  "contributing_factors": ["list of contributing factors"],
  "immediate_fix": "step-by-step immediate remediation",
  "runbook": ["ordered list of investigation/fix steps"],
  "prevention": "how to prevent this from recurring",
  "post_mortem_summary": "3-paragraph post-mortem"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"root_cause": raw, "contributing_factors": [], "immediate_fix": "", "runbook": [], "prevention": ""}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"analyze_incident #{incident.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            # If critical incident, require permission to post remediation to Slack/PagerDuty
            if incident.severity in ['high', 'critical']:
                raise PermissionRequired(
                    context=f"Critical incident #{incident.pk} analyzed. Root cause identified: {res.get('root_cause')}",
                    option_a="Approve posting remediation runbook to Slack #incidents",
                    option_b="Deny (Human will handle)"
                )
        return res

    def pipeline_health_check(self, pipeline, instance=None) -> dict:
        prompt = f"""Assess this CI/CD pipeline's health.

Pipeline: {pipeline.name}
Repository: {pipeline.repo_url}
Provider: {pipeline.provider}
Last Status: {pipeline.last_status}
Last Run: {pipeline.last_run_at}

Return JSON:
{{
  "health_score": integer 0-100,
  "status_assessment": "what this pipeline status means",
  "risks": ["potential issues if this continues"],
  "recommended_actions": ["specific actions to improve health"],
  "alert_level": "none|warning|critical"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"health_score": 50, "status_assessment": raw, "risks": [], "recommended_actions": [], "alert_level": "warning"}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"pipeline_health_check #{pipeline.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def deployment_checklist(self, service: str, change_description: str, instance=None) -> list:
        prompt = f"""Generate a production deployment checklist.

Service: {service}
Change: {change_description}

Return a JSON array of checklist items:
{{"step": "step description", "responsible": "who does this", "verify": "how to verify it worked", "rollback": "how to rollback if it fails"}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = []

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"deployment_checklist for {service}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def infrastructure_recommendations(self, pipeline_stats: dict, instance=None) -> str:
        stats_text = "\n".join(f"{k}: {v}" for k, v in pipeline_stats.items())
        prompt = f"""Review these infrastructure metrics and provide optimisation recommendations.

Metrics:
{stats_text}

Provide:
1. Top 3 reliability improvements (with estimated impact)
2. Cost optimisation opportunities
3. Security hardening priorities
4. Monitoring gaps to fill"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="infrastructure_recommendations",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
