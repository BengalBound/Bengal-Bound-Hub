# Bengal Bound — Cash Agent

## Purpose
Cash is the Payroll Processor AI employee. It processes payroll, calculates deductions, and generates payslips automatically — payroll in 5 minutes.

## Phase
Phase 3

## File Structure
```
cash/
├── __init__.py
├── apps.py
├── models.py          # Employee, PayrollRun
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

## Models

### `Employee`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| employee_id | CharField | Staff ID |
| name | CharField | Full name |
| email | EmailField | Work email |
| department | CharField | Department name |
| join_date | DateField | Start date |
| basic_salary | DecimalField | Gross base |
| house_rent | DecimalField | HRA allowance |
| medical | DecimalField | Medical allowance |
| bank_account | CharField | Account number |
| bank_name | CharField | Bank name |
| tin_number | CharField | Tax ID (optional) |
| pf_enrolled | BooleanField | Provident fund |
| is_active | BooleanField | Active flag |

### `PayrollRun`
| Field | Type | Notes |
|-------|------|-------|
| id | Auto | PK |
| organization | FK | Multi-tenant scope |
| month | DateField | Pay period (YYYY-MM-01) |
| total_gross | DecimalField | Total gross pay |
| total_net | DecimalField | Total net pay |
| total_tax | DecimalField | Total tax deducted |
| employee_count | IntegerField | Headcount |
| status | CharField | draft / approved / transferred |
| ai_summary | TextField | AI narrative |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/cash/employees/` | List employees |
| POST | `/api/v1/cash/employees/` | Add employee |
| GET | `/api/v1/cash/runs/` | List payroll runs |
| POST | `/api/v1/cash/runs/` | Create payroll run |
| POST | `/api/v1/cash/runs/{id}/summarise/` | **AI @action** — generate payroll summary |

## AI @Action

### `summarise` on `PayrollRun`
Calls `ai_chat()` with run totals and employee count. Writes `ai_summary`. Creates `AuditLog` entry.

## Channel Integration
- **Agent slug**: `cash`
- **Channels**: `chat`, `api`

## Running Locally
```bash
cd api && python manage.py migrate && python manage.py runserver
curl http://localhost:8000/api/v1/cash/employees/
```
