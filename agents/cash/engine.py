import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

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

    def generate_payroll_summary(self, run, instance=None) -> str:
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
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"generate_payroll_summary for run {run.pk}",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def calculate_net_pay(self, employee, instance=None) -> dict:
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
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"gross": 0, "tax": 0, "pf_deduction": 0, "net": 0, "calculation_steps": [raw]}
            
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"calculate_net_pay for employee {employee.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def anomaly_check(self, current_run, previous_totals: dict, instance=None) -> list:
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
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = []
            
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"anomaly_check for run {current_run.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
            
            has_critical = any(a.get("severity") == "critical" for a in res)
            if has_critical:
                raise PermissionRequired(
                    context=f"CRITICAL Payroll Anomalies detected for {current_run.month}. E.g.: {res[0].get('anomaly')}",
                    option_a="Approve and proceed with payroll processing",
                    option_b="Deny (Hold payroll for manual review)"
                )
        return res

    def compliance_check(self, employee, instance=None) -> dict:
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
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"compliant": True, "issues": [], "recommendations": []}
            
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"compliance_check for employee {employee.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
