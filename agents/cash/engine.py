import json
from agents.utils import agent_chat

SYSTEM_PROMPT = """You are Cash, BengalBound's AI Payroll Processor.

Your role is to ensure accurate, on-time payroll with zero errors. You handle calculations, compliance checks, and executive-level reporting.

Capabilities:
- Generate detailed payslip calculations with all deductions
- Identify payroll anomalies (unusual amounts, missing staff, mismatches)
- Produce executive payroll summaries with key metrics
- Flag compliance risks (tax underpayment, PF non-compliance)
- Answer payroll policy questions
- Recommend optimisations for salary structures

Principles:
- Accuracy is non-negotiable — flag anything uncertain for human review
- Compliance first: follow local tax and labour law requirements
- Privacy: never expose individual salary data in group summaries
- Always show calculation breakdowns, not just final numbers
- Flag anomalies immediately, don't suppress them

Jurisdiction: Bangladesh (BDT, income tax slabs, PF rules apply by default)"""


class CashEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def generate_payroll_summary(self, run) -> str:
        prompt = f"""Generate an executive payroll summary for this payroll run.

Period: {run.month}
Total Gross: BDT {run.total_gross:,.2f}
Total Net: BDT {run.total_net:,.2f}
Total Tax: BDT {run.total_tax:,.2f}
Employee Count: {run.employee_count}
Status: {run.status}

Write a concise executive summary covering:
1. Payroll health overview
2. Key metrics and comparisons (if available)
3. Any anomalies or flags
4. Recommended next steps"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return agent_chat(messages)

    def calculate_net_pay(self, employee) -> dict:
        prompt = f"""Calculate net pay for this employee.

Name: {employee.name}
Basic Salary: BDT {employee.basic_salary:,.2f}
House Rent Allowance: BDT {employee.house_rent:,.2f}
Medical Allowance: BDT {employee.medical:,.2f}
PF Enrolled: {employee.pf_enrolled}
TIN Number: {'Yes' if employee.tin_number else 'No'}

Calculate:
- Gross salary
- Income tax (Bangladesh tax slab)
- PF deduction (if enrolled: 10% basic)
- Net take-home pay

Return JSON with: gross, tax, pf_deduction, net, calculation_steps (list of strings)"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"gross": 0, "tax": 0, "pf_deduction": 0, "net": 0, "calculation_steps": [raw]}

    def anomaly_check(self, current_run, previous_totals: dict) -> list:
        prompt = f"""Check this payroll run for anomalies by comparing to previous period.

Current Period: {current_run.month}
Current Gross: BDT {current_run.total_gross:,.2f}
Current Employee Count: {current_run.employee_count}

Previous Period Totals:
{json.dumps(previous_totals, indent=2)}

List any anomalies as JSON array of objects:
{{"anomaly": "description", "severity": "low/medium/high/critical", "recommendation": "what to do"}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    def compliance_check(self, employee) -> dict:
        prompt = f"""Review this employee record for payroll compliance issues.

Employee: {employee.name}
Department: {employee.department}
Basic Salary: BDT {employee.basic_salary:,.2f}
PF Enrolled: {employee.pf_enrolled}
TIN: {'Present' if employee.tin_number else 'Missing'}
Join Date: {employee.join_date}

Return JSON with:
- "compliant": boolean
- "issues": list of compliance issues
- "recommendations": list of fixes"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"compliant": True, "issues": [], "recommendations": []}
