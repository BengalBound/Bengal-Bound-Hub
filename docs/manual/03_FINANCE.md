# Finance — Module Manual

**Modules covered:** Invoicing · Accounting · Payroll · Expense · Budgeting · Financials · Commission

---

## Accounting (`/hub/<slug>/accounting/`)

Double-entry bookkeeping for your business.

### Chart of Accounts
Hierarchical account structure:
- **Asset** — what you own (bank, receivables, equipment)
- **Liability** — what you owe (payables, loans)
- **Equity** — owner's stake
- **Income** — revenue accounts
- **Expense** — cost accounts

Each account has a code, name, currency, and optional parent for sub-accounts.

### Journal Entries
Every financial transaction is a journal entry with one or more lines:
- Each line debits or credits an account
- Entry types: sales, purchases, payroll, adjustment, bank transfer
- Status flow: `draft` → `posted` → `voided`

### Tax Rates
Define named tax rates (VAT, GST, withholding) as percentage or fixed. Assign to accounts.

### Fiscal Years
Set fiscal year start/end dates. Lock closed years to prevent backdating.

---

## Payroll (`/hub/<slug>/payroll/`)

Calculate and process employee salaries.

### Salary Structures
Define component bundles:
- **Earnings:** Basic salary, housing allowance, transport
- **Deductions:** Income tax, pension, provident fund
- Components can be fixed amounts, % of basic, or formula-based

### Pay Periods
Frequency: weekly / biweekly / monthly / quarterly

Status flow: `draft` → `processing` → `paid` → `cancelled`

### Payslips
Auto-generated per employee per pay period:
- Gross pay = sum of all earning components
- Net pay = gross pay − total deductions
- Status: `draft` → `confirmed` → `paid`

**AI Integration:** Hire **Cash** to audit payroll anomalies, flag unusual deductions, and send monthly payroll reminders.

---

## Expense (`/hub/<slug>/expense/`)

Employee expense reimbursement workflow.

### Expense Claim Flow
`draft` → `submitted` → `approved` / `rejected` → `paid`

### Expense Items
Each claim contains one or more items:
- Category (travel, meals, equipment, software, etc.)
- Amount, date, vendor, receipt upload
- Billable flag (for client-reimbursable expenses)

### Approval
Reviewers receive notification. They can approve with notes or reject with reason. Payment date recorded on payout.

---

## Budgeting (`/hub/<slug>/budgeting/`)

Department-level budget planning and variance tracking.

### Budget Periods
Define named periods with start/end dates (e.g. "FY2026 Q1").

### Budgets
- Assign budgets per department and period
- Status: `draft` → `approved` → `active` → `closed`
- Track budgeted vs actual amounts

### Budget Lines
Break each budget into account-level lines for granular control. Variance = actual − budgeted.

---

## Financials (`/hub/<slug>/financials/`)

Operational reporting and consolidated expenses.

### Operational Reports
Submit daily ops summaries, sales summaries, incident reports, and performance reviews by department:
- Status flow: `draft` → `submitted` → `approved` / `rejected`
- Reviewer adds notes before approving

### User Expenses
Simpler than Expense module — direct submission with department and category tagging.

---

## Commission (`/hub/<slug>/commission/`)

See [CRM & Sales Manual](02_CRM_AND_SALES.md#commission) for full details.

**AI Integration:** Hire **Reporting Bot** to auto-generate daily financial summaries across all finance modules.
