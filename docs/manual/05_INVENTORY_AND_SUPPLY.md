# Inventory & Supply Chain — Module Manual

**Modules covered:** Inventory · Order Management · Delivery · BOM · Production · Quality Control · Maintenance · WMS · TMS

---

## Inventory (`/hub/<slug>/inventory/`)

Multi-warehouse stock management with lot tracking.

### Products
- SKU, barcode, name, type (storable / consumable / service)
- Cost price and sale price (multi-currency)
- Reorder level and reorder quantity for auto-alert
- Units of measure with conversion ratios

### Warehouses
Multiple warehouses per business. Each has a manager and address.

### Stock Levels
Real-time quantities per product per warehouse (optionally per lot):
- Quantity on hand
- Reserved quantity (committed to orders)
- Available = on hand − reserved

### Stock Movements
Every stock change is a movement record:
- Types: inbound, outbound, transfer between warehouses, adjustment
- Status: `draft` → `confirmed` → `done`

### Lot Tracking
Optional lot/batch numbers with manufacturing and expiry dates. QMS status: `pending` / `passed` / `failed` / `bypass`.

**AI Integration:** Hire **Flux** for supply chain health monitoring, supplier risk alerts, and reorder recommendations.

---

## Order Management (`/hub/<slug>/orders/`)

Purchase order workflow for procurement.

### Vendors
Supplier records: contact, payment terms (net days), currency, tax ID.

### Purchase Orders
`draft` → `sent` → `confirmed` → `partial` → `received` → `cancelled`

Each PO line tracks: product, ordered qty, received qty, unit price. Currency, tax, and total auto-calculated.

**AI Integration:** Hire **Payload** for vendor assessment, RFQ processing, and price benchmarking.

---

## Delivery (`/hub/<slug>/delivery/`)

Last-mile delivery scheduling and tracking.

### Drivers
Driver records with vehicle details (type, plate), license number, and live status (available / on delivery / off duty).

### Delivery Zones
Geographic zones with base delivery fees.

### Delivery Orders
`pending` → `assigned` → `picked up` → `in transit` → `delivered` / `failed` / `returned`

Each order tracks: pickup/delivery addresses, contact windows, weight, special instructions, proof of delivery photo, and signature.

### Routes
Daily route plans assigning multiple delivery orders to one driver.

---

## BOM — Bill of Materials (`/hub/<slug>/bom/`)

Product recipe and component management.

### Bills of Materials
- Types: manufacture, phantom (virtual), kit
- Version-controlled with status: `draft` → `active` → `obsolete`
- Quantity per unit with yield percentage

### Components
Each BOM line specifies: component product, quantity, unit of measure, scrap %, tooling consumption.

### Work Centers
Define production resources (machines, workstations) with capacity and cost per hour.

### Operations
Manufacturing steps linked to work centers with sequence and duration.

---

## Production (`/hub/<slug>/production/`)

Manufacturing order execution.

### Manufacturing Orders
`draft` → `confirmed` → `in progress` → `done` → `cancelled`

Each MO references: product, BOM, target quantity, warehouse, and responsible person.

### Work Order Operations
Steps within an MO mapped to BOM operations:
- Status: `pending` → `ready` → `in progress` → `done` / `blocked`
- Actual vs planned duration, assigned worker

### Material Consumption
Record actual material used per MO:
- Consumed lot, consumed qty, actual scrap
- Compares against planned BOM quantities for variance

---

## Quality Control (`/hub/<slug>/quality/`)

AQL-based inspection management.

### AQL Standards
Define accept/reject thresholds by batch size range and sample size.

### Inspection Templates
Pre-built checklists for products — criteria can be pass/fail, numeric, or text.

### Inspections
- Types: incoming, in-process, final, audit
- Sample size tested, failed sample count
- Result: `pending` → `pass` / `fail` / `conditional`

---

## Maintenance (`/hub/<slug>/maintenance/`)

Preventive maintenance and work order management.

### Assets
Equipment, vehicles, buildings, IT, tools — with serial number, warranty, status, and assigned department.

### Maintenance Schedules
Recurring maintenance plans: daily / weekly / monthly / quarterly / annual.

### Work Orders
`open` → `assigned` → `in progress` → `on hold` → `completed` / `cancelled`

Track: corrective vs preventive type, priority, downtime hours, labour and parts costs, resolution notes.

---

## WMS — Warehouse Management (`/wms/` — suite prefix)

Advanced warehouse operations: bin locations, put-away rules, pick lists, and cycle counts. Works with Inventory module for stock levels.

---

## TMS — Transport Management (`/tms/` — suite prefix)

Freight and shipment management.

### Carriers
Define carriers by transport type: road, air, sea, rail, courier, intermodal.

### Routes
Origin → destination routes with distance, estimated hours, preferred carrier, and base cost.

### Shipments
Full shipment lifecycle from booking to delivery with carrier, route, and customer reference tracking.
