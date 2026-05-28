import json
from agents.utils import agent_chat

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

    def nl_to_sql(self, query) -> dict:
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
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"generated_sql": raw, "plain_english_explanation": "", "assumptions": [], "warnings": []}

    def analyse_results(self, question: str, results: list, source_type: str) -> str:
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
        return agent_chat(messages)

    def anomaly_detection(self, dataset_description: str, sample_data: list) -> dict:
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
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"anomalies_found": False, "anomalies": [], "data_quality_score": 80, "recommendations": []}

    def visualisation_suggestions(self, query: str, results_schema: list) -> list:
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
            return json.loads(raw)
        except json.JSONDecodeError:
            return []
