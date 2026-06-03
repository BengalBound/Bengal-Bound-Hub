# Specialty Modules — Manual

**Modules covered:** Garden Ops · Care Manager (Field Services)

---

## Garden Ops (`/hub/<slug>/garden/`)

Job management for landscaping companies, nurseries, and florists.

### Client Sites
Each customer location is a site record:
- Site types: residential, commercial, public space, estate, other
- Area (sqm), contact details, assigned staff
- Active/inactive status

### Garden Jobs
Work orders for site visits:
- Job types: mowing, planting, pruning, landscaping, irrigation, weeding, seasonal maintenance, other
- Status: `pending` → `scheduled` → `in progress` → `completed` / `cancelled`
- Scheduled date and actual completion date
- Assigned staff members
- Estimated and actual hours and costs
- Job notes

### Garden Inventory
Stock management for plant and landscaping materials:
- Categories: plants, tools, chemicals, materials, pots, other
- Quantity on hand, unit, cost per unit
- Supplier and low-stock threshold
- Reorder alerts when below threshold

---

## Care Manager (`/hub/<slug>/care/`)

Personal care and home care business operations.

See [Healthcare Manual](08_HEALTHCARE.md) for full detail. Key use cases beyond clinics:

### Salon & Spa Use
- Client records with service history and preferences
- Appointment tracking via Booking module
- Staff rota management

### Home Care Use
- Care client records with assigned care workers
- Care plans (personal, medical, social, dietary)
- Session logs for compliance and CQC reporting
- Staff rota with shift confirmation

### Field Services (General)
- Any business with staff visiting client sites
- Job scheduling and completion tracking
- Route planning and mileage logging

---

## Process Mapper (`/process-mapper/` — suite prefix)

See [Analytics Manual](14_ANALYTICS.md#process-mapper) for full detail.

Key use cases for specialty businesses:

| Business | Use Case |
|----------|----------|
| Landscaping | Document quote-to-job workflow |
| Care facility | CQC-compliant care delivery processes |
| Salon | Client journey from booking to checkout |
| Logistics | Delivery and exception handling flowcharts |

---

## Call Center (`/hub/<slug>/call-center/`)

See [Analytics Manual](14_ANALYTICS.md#call-center) for full detail.

Works for any business that handles inbound phone calls at volume — clinics, salons, home care, logistics dispatch, and hospitality.
