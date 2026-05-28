import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Nova, BengalBound's AI Data Scientist.

Your role is to turn raw data into competitive intelligence. You translate plain-English business questions into precise SQL, run analysis, and surface insights that drive decisions.

Capabilities:
- Translate natural-language questions into production-ready SQL queries
- Analyse query results and extract business insights
- Detect data anomalies, trends, and outliers
- Generate data visualisation recommendations
- Build scheduled data reports for executives
- Assess data quality and flag reliability issues

Principles:
- SQL safety first: never generate DROP, TRUNCATE, DELETE without explicit confirmation
- Always SELECT, never mutate, unless explicitly asked
- Explain SQL in plain English alongside the query
- Validate assumptions: if the question is ambiguous, state your interpretation
- Results should be interpreted, not just presented — explain what the numbers mean
- Flag data quality issues that affect the analysis

SQL safety rules: Read-only queries only (SELECT). Parameterise inputs. Avoid subquery bombs on large tables."""


class NovaEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def nl_to_sql(self, query, instance=None) -> dict:
        schema_hint = f"Source type: {query.data_source.source_type}" if query.data_source else "Schema not specified"
        prompt = f"""Translate this business question into a SQL query.

Question: {query.question}
{schema_hint}

Return JSON:
{{
  "generated_sql": "the SELECT query",
  "plain_english_explanation": "what this query does in plain English",
  "assumptions": ["assumptions made about the data structure"],
  "warnings": ["any caveats about accuracy or data quality"],
  "alternative_interpretations": ["if the question was ambiguous, other ways to read it"]
}}

IMPORTANT: Generate only SELECT statements. No mutations."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"generated_sql": raw, "plain_english_explanation": "", "assumptions": [], "warnings": []}
            
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"nl_to_sql for {query.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
            
            sql_upper = res.get("generated_sql", "").upper()
            if any(mutation in sql_upper for mutation in ["DROP", "TRUNCATE", "DELETE", "UPDATE", "INSERT"]):
                raise PermissionRequired(
                    context=f"DANGEROUS SQL generated: {res.get('generated_sql')}",
                    option_a="Approve and execute mutation",
                    option_b="Deny and discard query"
                )
        return res

    def analyse_results(self, question: str, results: list, source_type: str, instance=None) -> str:
        results_text = json.dumps(results[:20], indent=2) if results else "No results returned"
        prompt = f"""Analyse these query results and provide business insights.

Original Question: {question}
Data Source: {source_type}
Results (sample):
{results_text}

Provide:
1. Direct answer to the original question
2. Key trends or patterns in the data
3. Anomalies or unexpected findings
4. 2-3 actionable recommendations based on these insights
5. Data quality notes (if any issues detected)"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="analyse_results",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def anomaly_detection(self, dataset_description: str, sample_data: list, instance=None) -> dict:
        data_text = json.dumps(sample_data[:30], indent=2)
        prompt = f"""Detect anomalies in this dataset.

Dataset: {dataset_description}
Sample data:
{data_text}

Return JSON:
{{
  "anomalies_found": boolean,
  "anomalies": [
    {{"field": "...", "issue": "...", "severity": "low|medium|high", "affected_rows_estimate": "..."}}
  ],
  "data_quality_score": integer 0-100,
  "recommendations": ["how to address each anomaly"]
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"anomalies_found": False, "anomalies": [], "data_quality_score": 80, "recommendations": []}
            
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="anomaly_detection",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def visualisation_suggestions(self, query: str, results_schema: list, instance=None) -> list:
        schema_text = ", ".join(results_schema)
        prompt = f"""Recommend the best data visualisations for this query result.

Query: {query}
Result columns: {schema_text}

Return a JSON array of visualisation recommendations:
{{
  "chart_type": "bar|line|pie|scatter|heatmap|table|metric",
  "x_axis": "field name",
  "y_axis": "field name or aggregation",
  "rationale": "why this chart works",
  "tool": "recommended tool (Tableau, PowerBI, Chart.js, etc.)"
}}"""

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
                action="visualisation_suggestions",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
