# Automotive — Module Manual

**Modules covered:** Workshop · DVI · DMS

---

## Workshop (`/workshop/` — suite prefix)

Job card and repair order management for garages, mechanics, and service centres.

### Job Cards
Each vehicle service creates a job card:
- Vehicle details: registration, make, model, year, mileage
- Customer: name, phone, email
- Job type: service, repair, MOT, diagnostic, bodywork, custom
- Status: `open` → `in progress` → `awaiting parts` → `completed` → `invoiced` → `closed`

### Technician Assignment
Assign specific technicians to job cards. Track labour hours logged per technician.

### Parts Used
Record parts consumed on each job:
- Part name, part number, quantity, unit cost
- Linked to inventory if tracked stock

### Labour
Log technician time per operation:
- Labour type: standard, diagnostic, bodywork
- Time taken, rate per hour

**AI Integration:** Hire **Kai** for DevOps monitoring of workshop software and infrastructure.

---

## DVI — Digital Vehicle Inspection (`/dvi/` — suite prefix)

Paperless vehicle inspection reports with photo documentation.

### Inspection Templates
Customisable checklists per vehicle type or inspection type:
- Checkpoints defined as JSON (name, category, inspection instructions)

### Vehicle Inspections
Full inspection workflow:
- Inspection number, template used
- Vehicle details: make, model, year, VIN, registration, mileage
- Customer name, job card number reference
- Overall result: `pass` / `advisory` / `fail` / `incomplete`
- Performed by, inspected at

### Inspection Items
Checkpoint-by-checkpoint results:
- Status per item: `ok` / `attention` / `critical` / `N/A`
- Notes and photo per item
- Ordered by category (tyres, brakes, lights, fluid levels, bodywork, etc.)

### Customer Sharing
Generate a shareable report link (share token). Flag as sent when emailed to customer.

---

## DMS — Dealer Management System (`/dms/` — suite prefix)

Full dealership inventory and sales management.

### Vehicle Stock
New and used vehicle inventory:
- Stock number, make, model, variant, year, colour
- VIN, registration, engine size, transmission, fuel type
- Body type, doors, seats, mileage
- Stock type: `new` / `used` / `CPO` (Certified Pre-Owned) / `demo`
- Status: `in stock` / `reserved` / `sold` / `awaiting prep` / `in transit`
- Purchase price, asking price, reserve price
- Main photo and detailed description

### Vehicle Photos
Multiple photos per vehicle with caption and display order.

### Vehicle Deals
Sales pipeline per vehicle:
- Deal number, assigned vehicle
- Stage (configurable pipeline stages)
- Customer contact details
- Sale price, deposit amount
- Finance: type (PCP/HP/lease/cash), provider, amount, monthly repayment, loan term
- Salesperson, notes, test drive date, expected delivery date

### Trade-Ins
Record trade-in vehicles against a deal:
- Make, model, year, registration, VIN, mileage, condition
- Offered price and accepted price
- Notes on condition

### Deal Notes
Internal notes per deal — visible to the sales team only.
