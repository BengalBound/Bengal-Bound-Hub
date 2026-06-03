# BengalBound HUB — User Manual

**Version:** 1.1 · June 2026  
**Live URL:** `https://bengal-bound-hub-u5i67kezxa-vp.a.run.app`  
**Dev URL:** `http://localhost:1234`

---

> Full manuals are in [`docs/manual/`](docs/manual/). This file is the index.

---

## Platform Flow

Start here if you are new:

**[docs/manual/00_PLATFORM_FLOW.md](docs/manual/00_PLATFORM_FLOW.md)**

Covers: registration → 2FA → business creation → team setup → module activation → hiring agents → autonomous operation → approval flow.

---

## Module Manuals

| # | Manual | Modules Covered |
|---|--------|----------------|
| 02 | [CRM & Sales](docs/manual/02_CRM_AND_SALES.md) | CRM, Leads, Invoicing, Contracts, Deal Flow, Commission, B2B Portal, Omnichannel |
| 03 | [Finance](docs/manual/03_FINANCE.md) | Accounting, Payroll, Expense, Budgeting, Financials |
| 04 | [HR & People](docs/manual/04_HR_AND_PEOPLE.md) | HR, Recruitment, Attendance, Shift Planning, Training, LMS, Assessments |
| 05 | [Inventory & Supply Chain](docs/manual/05_INVENTORY_AND_SUPPLY.md) | Inventory, Order Mgmt, Delivery, BOM, Production, QC, Maintenance, WMS, TMS |
| 06 | [Retail & Commerce](docs/manual/06_RETAIL_AND_COMMERCE.md) | POS, eCommerce, Loyalty, Planogram, Store Ops, Product Catalog, Table Mgmt |
| 07 | [Hospitality](docs/manual/07_HOSPITALITY.md) | PMS, Channel Manager, Rate Manager, Booking, Group Bookings, Hospitality Ops |
| 08 | [Healthcare](docs/manual/08_HEALTHCARE.md) | Care Manager, Booking |
| 09 | [Education](docs/manual/09_EDUCATION.md) | SIS, LMS, Assessments, Timetable, Parent Portal |
| 10 | [Real Estate](docs/manual/10_REAL_ESTATE.md) | Property Listings, Deal Flow, RE Marketing, RE Client Portal, Commission |
| 11 | [Manufacturing](docs/manual/11_MANUFACTURING.md) | ERP, MES, PLM, BOM, Production, QC, Asset Management, CAD/CAM |
| 12 | [Travel](docs/manual/12_TRAVEL.md) | Travel CRM, Travel Desk, Group Bookings |
| 13 | [Productivity & Communication](docs/manual/13_PRODUCTIVITY.md) | Mail, Video Meet, Calendar, Drive, Docs, Sheets, Slides, Forms, Chat, Announcements, Task Board, Projects |
| 14 | [Analytics & Intelligence](docs/manual/14_ANALYTICS.md) | Reports, AI Analytics, AI Assistant, Data Studio, Dashboard Pro, Data Collection, Process Mapper, Call Center |
| 15 | [Automotive](docs/manual/15_AUTOMOTIVE.md) | Workshop, DVI, DMS |
| 16 | [Specialty](docs/manual/16_SPECIALTY.md) | Garden Ops, Care Manager (field services) |
| 17 | [AI Agents](docs/manual/17_AI_AGENTS.md) | All 33 agents — hiring, workspace, schedules, permissions, REST API |

---

## Quick Reference

### Key URLs

| Purpose | URL |
|---------|-----|
| Admin panel | `/admin/` |
| Register | `/accounts/signup/` |
| Login | `/accounts/login/` |
| Business Hub | `/hub/<slug>/` |
| Console | `/console/` |
| Agents overview | `/console/agents/` |
| Hire an agent | `/console/hire-ai/` |
| Billing | `/console/billing/` |
| 2FA setup | `/console/security/totp/setup/` |
| Notifications | `/console/notifications/` |
| API docs | `/api/docs/` |

### Start Dev Server
```powershell
python manage.py runserver 0.0.0.0:1234
```

### Seed Everything
```powershell
python manage.py migrate
python manage.py seed_modules    # 83 business modules
python manage.py seed_agents     # 33 AI agents
python manage.py createsuperuser
```

### Start Celery (for scheduled agent tasks)
```powershell
celery -A bengalbound_core worker --loglevel=info
celery -A bengalbound_core beat --loglevel=info
```

### Run Tests
```powershell
python -m pytest
```

---

## UAT Test Cases

See the original `USER_MANUAL.md` content (archived below) for the full UAT test case blocks A–J.

The UAT suite covers:
- **Block A** — Authentication (register, verify, login, TOTP, rate-limiting)
- **Block B** — Business & module setup
- **Block C** — Agent hiring overview
- **Block D** — Agent workspace & chat
- **Block E** — Agent REST API
- **Block F** — Approval & permission flow
- **Block G** — Scheduled Celery tasks
- **Block H** — Security (CSRF, HMAC, axes)
- **Block I** — Design & responsiveness
- **Block J** — End-to-end happy path (16-step smoke test)
