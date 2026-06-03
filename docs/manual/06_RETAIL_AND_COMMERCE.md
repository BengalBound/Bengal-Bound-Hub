# Retail & Commerce — Module Manual

**Modules covered:** POS · eCommerce · Loyalty · Planogram · Store Ops · Product Catalog · Table Management

---

## POS — Point of Sale (`/hub/<slug>/pos/`)

Full retail point-of-sale system.

### POS Config
Configure your till: receipt header/footer, tax rate, currency, discount rules, cash rounding.

### Sessions
Every cashier opens a session with an opening cash amount. Close the session at end of shift — system totals all cash, card, and mixed payments.

### Orders
Each sale creates an order:
- Status: `open` → `paid` → `refunded` / `cancelled`
- Payment methods: cash, card, mixed, pending (for layaway)
- Subtotal, tax, discount, total, amount tendered, change due
- Customer name for receipt personalisation

### Order Items
Linked to inventory products or typed ad-hoc. Supports quantity and per-item discounts.

**AI Integration:** Hire **Merch** for daily stock level alerts and low-inventory notifications.

---

## eCommerce (`/hub/<slug>/ecommerce/`)

Online store management.

### Stores
Each business can have one or more online stores with its own slug, currency, and tax rate.

### Products
- Types: physical, digital, service
- SKU, price, compare price (for showing discounts), cost
- Stock tracking with backorder option
- Status: `draft` → `active` → `archived`

### Categories
Hierarchical product categories with description and image.

### Orders
Full order lifecycle: customer info, shipping/billing addresses, payment method, tracking number, fulfilment notes.

**AI Integration:** Hire **Merch** to optimise listings, monitor competitor pricing, and manage reorder levels.

---

## Loyalty (`/hub/<slug>/loyalty/`)

Points-based customer loyalty programme.

### Programs
- Reward types: points, cashback, tiered
- Points per currency unit spent
- Minimum redemption threshold
- Points expiry (configurable in days)

### Tiers
Named tiers (Bronze / Silver / Gold / Platinum) with min points, point multiplier, and benefits list.

### Members
Customer loyalty cards:
- Total points, lifetime points, total spend
- Tier auto-upgrades as points accumulate

### Point Transactions
Every earn / redeem / expire / adjustment is logged with description and reference.

---

## Planogram (`/planogram/` — suite prefix)

Store shelf layout planning.

### Store Layouts
Define store floor plans with named sections.

### Planogram Slots
Each slot specifies: product, shelf number, position, number of facings, minimum stock, current stock, reorder flag.

Use planograms to ensure products are stocked and placed consistently across store locations.

---

## Store Ops (`/store-ops/` — suite prefix)

Multi-store operations management.

### Stores
Retail store records: address, manager, opening/closing times.

### Daily Reports
Submitted per store per day: sales total, transaction count, top-selling product. Managers review and compare across locations.

### Tasks
Assign compliance or operational tasks to store staff with due dates and priority.

---

## Product Catalog (`/product-catalog/` — suite prefix)

Public-facing product catalogue — shareable with customers.

- Create named catalogues (e.g. "2026 Spring Collection")
- Categorise items with display order
- Each item: name, SKU, price, unit, featured flag, in-stock status
- Public URL and share token for external access

---

## Table Management (`/hub/<slug>/tables/`)

Restaurant floor plan and reservation system.

### Dining Areas
Named sections of the restaurant floor (e.g. "Main Hall", "Terrace", "Private Dining").

### Tables
Each table has: number, capacity, shape (square/round/rectangle), X/Y position on floor plan, and live status:
- `available` — ready to seat
- `occupied` — guests seated
- `reserved` — booking confirmed
- `cleaning` — being turned around
- `inactive` — not in service

### Reservations
Book specific tables: guest name, party size, date, time, duration, occasion, special requests.
Status: `pending` → `confirmed` → `seated` → `completed` / `cancelled` / `no show`

### Table Orders
Open a tab per table: server assigned, cover count, subtotal/tax/tip/discount, open/close time.
