import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Reporting Bot, BengalBound's AI Automated Reporting Specialist.

Your role is to transform raw KPI data into clear, decision-ready reports that executives actually read. You narrate numbers with context, highlight what matters, and recommend actions.

Capabilities:
- Generate narrative business reports from KPI data
- Identify trends, anomalies, and period-over-period changes
- Write executive summaries that lead with the most important insight
- Build scheduled report templates for recurring delivery
- Highlight performance outliers (both positive and negative)
- Translate metrics into business implications

Principles:
- Lead with the insight, not the data — "revenue is down 12% because X" not just "revenue is down 12%"
- Every metric should be contextualised: vs. last period, vs. target, vs. industry
- Anomalies deserve emphasis and explanation
- Recommendations must be specific: "increase ad spend by 20% on Thursdays" not "increase marketing"
- Avoid data dumps — select the 5-7 most important metrics per report
- Reports should take < 5 minutes to read and act on

Report frequency: weekly, biweekly, monthly"""


class ReportingBotEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def generate_narrative(self, report, config, instance=None) -> str:
        kpis_text = json.dumps(config.kpis, indent=2) if config.kpis else "KPIs not configured"
        sources_text = ", ".join(config.data_sources) if config.data_sources else "Not specified"

        prompt = f"""Generate an executive report narrative.

Report: {config.report_name}
Period: {report.period_start} to {report.period_end}
Frequency: {config.frequency}
Data Sources: {sources_text}
KPI Definitions:
{kpis_text}

Write a professional report narrative that:
1. Opens with an executive summary (2 sentences: what happened and what it means)
2. Reports each KPI with context and trend
3. Highlights top 2 positive developments
4. Highlights top 2 concerns with root cause hypothesis
5. Closes with 3 specific recommended actions for next period

Write in clear, executive-friendly language."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"generate_narrative {report.pk}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def anomaly_highlight(self, kpi_name: str, current_value: float, previous_value: float, target: float = None, instance=None) -> dict:
        change_pct = ((current_value - previous_value) / previous_value * 100) if previous_value else 0
        target_text = f"Target: {target}" if target else "No target set"

        prompt = f"""Analyse this KPI anomaly.

KPI: {kpi_name}
Current: {current_value}
Previous Period: {previous_value}
Change: {change_pct:+.1f}%
{target_text}

Return JSON:
{{
  "is_anomaly": boolean,
  "severity": "none|minor|significant|critical",
  "explanation": "likely cause of this change",
  "action_required": boolean,
  "recommended_action": "specific action if required"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"is_anomaly": abs(change_pct) > 15, "severity": "significant" if abs(change_pct) > 15 else "minor", "explanation": raw, "action_required": False}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"anomaly_highlight for {kpi_name}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if res.get("severity") == "critical":
                raise PermissionRequired(
                    context=f"CRITICAL anomaly detected in KPI: {kpi_name}. Reason: {res.get('explanation')}",
                    option_a="Acknowledge and flag to executive team",
                    option_b="Ignore anomaly"
                )
        return res

    def executive_summary(self, report, kpi_results: list, instance=None) -> str:
        kpi_text = "\n".join(
            f"- {k.get('name', 'KPI')}: {k.get('value', 'N/A')} (prev: {k.get('previous', 'N/A')})"
            for k in kpi_results[:10]
        )
        prompt = f"""Write a 3-sentence executive summary for this report.

Period: {report.period_start} to {report.period_end}
KPI Results:
{kpi_text}

Write ONLY 3 sentences: (1) overall business performance verdict, (2) most important positive, (3) most important concern."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"executive_summary {report.pk}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
