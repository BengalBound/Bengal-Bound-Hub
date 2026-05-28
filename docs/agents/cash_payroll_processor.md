# Module Requirements: Cash — AI Payroll Processor
# BengalBound HUB Integration

> **Prepared for:** Bengal Bound | **Date:** April 2026 | **Version:** 1.0
> 🔧 Django + DRF — `cash` app | 🤖 LiteLLM proxy (Gemini 1.5 Flash via LITELLM_BASE_URL) | ☁️ Django + Celery (BengalBound HUB deployment)

---

## Section 1: Overview

**AI Employee Name:** Cash | **Department:** Finance / HR Operations
**Core Function:** Processes monthly payroll automatically — calculates net pay including statutory deductions, generates PDF payslips, prepares bank transfer files, and ensures full compliance with Bangladesh Labour Law 2006 and applicable tax regulations.
**Value Prop:** *"Payroll done in 5 minutes, not 5 days. Every employee paid correctly and on time."*

---

## Section 2: Core Capabilities

1. **Employee Registry** — Full records: basic salary, allowances, deductions, tax bracket, bank details, PF enrollment
2. **Payroll Calculation** — Gross → statutory deductions (income tax, provident fund, ESSO) → net pay per BD Labour Law + Finance Act
3. **Payslip Generation** — Professional PDF payslips auto-emailed to each employee on payroll run
4. **Bank Transfer File** — BEFTN-format payment file for bank upload; bKash/Nagad direct API for mobile wallet payroll
5. **Tax Withholding Tracker** — Monthly TDS tracking per employee; annual salary certificate for tax returns
6. **Leave & Overtime Integration** — Pulls approved leave; adjusts for unpaid leave and overtime
7. **Payroll Audit Trail** — Immutable record of every payroll run; exportable for audit
8. **Compliance Alerts** — Alerts when minimum wage, tax slabs, or PF rates change

---

## Section 3: Django Models

```python
class Employee(models.Model):
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='cash_employees')
    employee_id     = models.CharField(max_length=50)
    name            = models.CharField(max_length=300)
    email           = models.EmailField()
    department      = models.CharField(max_length=200)
    join_date       = models.DateField()
    basic_salary    = models.DecimalField(max_digits=12, decimal_places=2)
    house_rent      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medical         = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bank_account    = models.CharField(max_length=100)
    bank_name       = models.CharField(max_length=200)
    tin_number      = models.CharField(max_length=50, blank=True)
    pf_enrolled     = models.BooleanField(default=False)
    is_active       = models.BooleanField(default=True)

class PayrollRun(models.Model):
    STATUS = [('draft','Draft'),('approved','Approved'),('transferred','Transferred')]
    business        = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='cash_payrollruns')
    month           = models.DateField()
    total_gross     = models.DecimalField(max_digits=14, decimal_places=2)
    total_net       = models.DecimalField(max_digits=14, decimal_places=2)
    total_tax       = models.DecimalField(max_digits=14, decimal_places=2)
    employee_count  = models.IntegerField()
    status          = models.CharField(max_length=20, choices=STATUS, default='draft')
    approved_by     = models.CharField(max_length=200, blank=True)
    transferred_at  = models.DateTimeField(null=True)
    created_at      = models.DateTimeField(auto_now_add=True)

class PayslipRecord(models.Model):
    payroll_run     = models.ForeignKey(PayrollRun, on_delete=models.CASCADE)
    employee        = models.ForeignKey(Employee, on_delete=models.CASCADE)
    gross_pay       = models.DecimalField(max_digits=12, decimal_places=2)
    income_tax      = models.DecimalField(max_digits=12, decimal_places=2)
    provident_fund  = models.DecimalField(max_digits=12, decimal_places=2)
    net_pay         = models.DecimalField(max_digits=12, decimal_places=2)
    payslip_pdf     = models.FileField(upload_to='payslips/')
    email_sent      = models.BooleanField(default=False)
```

---

## Section 4: API Endpoints (`/hub/<slug>/api/agents/cash/`)

| Method | Endpoint | Action |
|---|---|---|
| `GET/POST` | `/employees/` | Manage employee records |
| `POST` | `/payroll/run/` | Initiate monthly payroll |
| `GET` | `/payroll/{id}/` | Payroll run detail |
| `POST` | `/payroll/{id}/approve/` | Approve + initiate transfer |
| `GET` | `/payroll/{id}/payslips/` | Payslips for a run |
| `GET` | `/tax-summary/{year}/` | Annual TDS report |
| `GET` | `/compliance/alerts/` | Labour law / tax change alerts |

---

## Section 5: Tech Stack & Delivery

```
pip install reportlab django-apscheduler requests
```

> All AI calls route through the LiteLLM proxy (`LITELLM_BASE_URL`). Use `agent_chat()` from `agents.utils` — never call Gemini directly.

| Phase | Scope | Timeline |
|---|---|---|
| Phase 1 | Employee registry, calculation, PDF payslips, email delivery | Weeks 1–5 |
| Phase 2 | Tax tracking, PF, BEFTN export, approval workflow | Weeks 6–10 |
| Phase 3 | bKash/Nagad transfer, leave integration, annual tax cert | Weeks 11–16 |

| Tier | Monthly | Employees | Features |
|---|---|---|---|
| Intern | Free | 5 | Payslips only |
| Entry | ৳2,000 | 25 | Bank file, tax tracking |
| Mid | ৳5,000 | 100 | Mobile wallet, leave integration |
| Senior | ৳10,000 | Unlimited | Full compliance, audit trail |

*BengalBound HUB — dev branch*
