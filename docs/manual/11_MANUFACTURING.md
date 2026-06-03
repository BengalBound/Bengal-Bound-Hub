# Manufacturing — Module Manual

**Modules covered:** ERP · MES · PLM · BOM · Production · Quality Control · Asset Management · CAD/CAM

---

## ERP — Enterprise Resource Planning (`/erp/` — suite prefix)

Core accounting ledger integrated with all manufacturing operations.

### ERP Ledger
Hierarchical chart of accounts:
- Types: asset, liability, equity, revenue, expense
- Parent/child relationships for sub-accounts

### Journal Entries
All financial transactions from manufacturing operations post here:
- Status: `draft` → `posted` → `reversed`
- Reference numbers for audit trail

*ERP integrates with Production, Payroll, Inventory, and Invoicing for unified financial reporting.*

---

## MES — Manufacturing Execution System (`/mes/` — suite prefix)

Real-time shop floor tracking and execution.

### Work Centers
Physical production resources:
- Status: `active` / `idle` / `maintenance` / `offline`
- Capacity per hour, operator assignment, machine ID

### Routings
Sequences of work center operations that define how a product is made.

Each routing station has: work center, sequence number, bottleneck flag.

### Production Orders
Shop floor execution records:
- Status: `planned` → `released` → `in progress` → `paused` → `completed` / `cancelled`
- Tracks: planned vs produced quantities, current station, actual start/end times

---

## PLM — Product Lifecycle Management (`/plm/` — suite prefix)

Engineering and product development management.

### Products (Engineering)
Products tracked from concept to end-of-life:
- Stages: concept → design → prototype → testing → production → EOL → obsolete
- Version and revision control
- Owner assignment

### Bills of Materials
Version-controlled BOMs linked to PLM products:
- BOM lines: item code, quantity, unit, reference designator, substitute flag

### Engineering Change Orders (ECO)
Formal process to change a product design:
- Status: `draft` → `submitted` → `under review` → `approved` / `rejected` → `implemented`
- Priority, reason, description, approver trail

### Product Documents
Technical files per product: drawings, specs, SOPs, test reports, certifications, user manuals.

---

## BOM — Bill of Materials (`/hub/<slug>/bom/`)

See [Inventory & Supply Chain Manual](05_INVENTORY_AND_SUPPLY.md#bom) for full details.

Footwear industry extension included: shoe article BOM, colorway entries, material consumption by category (upper / lining / footbed / adhesive).

---

## Production (`/hub/<slug>/production/`)

See [Inventory & Supply Chain Manual](05_INVENTORY_AND_SUPPLY.md#production) for full details.

---

## Quality Control (`/hub/<slug>/quality/`)

See [Inventory & Supply Chain Manual](05_INVENTORY_AND_SUPPLY.md#quality-control) for full details.

---

## Asset Management (`/hub/<slug>/assets/`)

Physical asset lifecycle and depreciation tracking.

### Assets
All physical assets: equipment, vehicles, buildings, IT hardware, tools.
- Asset tag, serial number, manufacturer, model
- Status: `active` / `idle` / `under maintenance` / `retired` / `disposed`
- Assigned to employee, location, department

### Asset Usage Logs
Record usage sessions: amount used, reference, recorded by.

### Maintenance Schedules
Planned maintenance: frequency (daily/weekly/monthly/quarterly/annual/on demand), next due date.

### Work Orders
Maintenance execution:
- Types: preventive, corrective, inspection, emergency
- Status: `open` → `assigned` → `in progress` → `completed` / `cancelled`
- Cost tracking: labour + parts

### Depreciation
Monthly depreciation records:
- Period, opening book value, depreciation amount, closing book value
- Auto-calculated from asset category depreciation rate and useful life

### Asset Documents
Attach manuals, warranty certificates, inspection reports, and invoices per asset.

---

## CAD/CAM (`/cadcam/` — suite prefix)

Engineering design file repository.

### CAD Projects
Design projects tracked by tool (Fusion 360, FreeCAD, CAMotics, other) and status.

### CAD Files
Version-controlled file uploads:
- Formats: STEP, IGES, STL, DXF, DWG, F3D, FreeCAD, G-code
- Version number and change description per upload
