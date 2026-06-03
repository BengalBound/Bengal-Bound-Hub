# Hospitality — Module Manual

**Modules covered:** PMS · Channel Manager · Rate Manager · Booking · Group Bookings · Hospitality Ops

---

## PMS — Property Management System (`/hub/<slug>/pms/`)

Hotel front desk operations.

### Room Types
Define room categories with: code, max occupancy, base rate, amenities list.

### Rooms
Individual rooms with: floor, status, and notes.

Room statuses:
- `available` — clean and ready
- `occupied` — guests in room
- `dirty` — needs housekeeping
- `maintenance` — out of service for repairs
- `blocked` — held for special use

### Guest Profiles
Persistent guest records: passport number, nationality, dietary notes, preferences. Linked to reservations.

### Reservations
Full reservation lifecycle:
`pending` → `confirmed` → `checked in` → `checked out` → `cancelled` / `no show`

Each reservation: guest, room, check-in/out dates, adults/children, source (direct / OTA / GDS / phone / walk-in), rate per night, total, currency.

**AI Integration:** Hire **Tempo** for group event coordination. Hire **Reporting Bot** for daily occupancy and RevPAR reports.

---

## Channel Manager (`/hub/<slug>/channels/`)

Distribute your rooms across online travel agencies and booking platforms.

### Channels
Connect to: Booking.com, Expedia, Airbnb, GDS, wholesalers, metasearch engines.

Per channel: API endpoint, API key, commission %, active flag.

### Rate Plans
Named rate bundles: Room Only (RO), Bed & Breakfast (BB), Half Board (HB), Full Board (FB), All Inclusive (AI).

Options: refundable, minimum stay, advance purchase.

### Channel Rates
Set specific rates per channel, per rate plan, per room type — with valid date ranges.

### Availability Blocks
Manage room inventory by date: available rooms, sold rooms, occupancy %.

### Sync Logs
Every sync operation (rates / availability / reservations / full sync) is logged with status and record count.

---

## Rate Manager (`/hub/<slug>/rates/`)

Revenue management and dynamic pricing.

### Seasons
Define demand seasons: peak, high, shoulder, low — each with a rate multiplier.

### Base Rates
Set base nightly rates per room type with effective date ranges.

### Yield Rules
Automatic pricing adjustments triggered by:
- **Occupancy** — raise rates when hotel is 80%+ full
- **Advance booking days** — early bird discounts at 60+ days out
- **Day of week** — weekend vs weekday pricing

Adjustment types: percentage increase/decrease or fixed amount.

### Rate Restrictions
Apply restrictions per room type and date range:
- Minimum stay / maximum stay
- Closed to arrival / closed to departure

### Special Offers
Promo codes and discount packages:
- Types: early bird, last minute, package, promotional
- Discount type: percentage or fixed amount
- Promo code for direct bookings

---

## Booking (`/hub/<slug>/booking/`)

Online appointment and room booking widget.

### Services
Each bookable service: name, duration, price, buffer time before/after, maximum concurrent bookings.

### Staff Availability
Set which staff members are available on which days and hours.

### Bookings
Customer self-books or staff books on their behalf:
Status: `pending` → `confirmed` → `completed` / `cancelled` / `no show` / `rescheduled`

**AI Integration:** Hire **MediBook** (clinics), **Tempo** (event spaces), or **Voice Receptionist** (phone bookings).

---

## Group Bookings (`/hub/<slug>/groups/`)

Multi-room group reservation management for events and conferences.

### Group RFPs
Request for Proposal workflow:
- Group name, contact, event type, arrival/departure, rooms required
- Status: `enquiry` → `proposal sent` → `contracted` → `confirmed` → `in-house` → `departed`

### Room Blocks
Hold specific room types for the group:
- Rooms blocked, rate per night, release date (rooms return to general inventory if not confirmed)

### Rooming List
Individual guest assignments within the group block.

### Group Contracts
Formal group agreement:
- Deposit amount, due date, paid status
- Total value, cancellation policy, attrition %
- Signed flag and signature date

---

## Hospitality Ops (`/hub/<slug>/hosp-ops/`)

Day-to-day hotel operations management.

### Housekeeping
Room cleaning task management:
- Task types: checkout clean, stayover, deep clean, turndown, inspection
- Assign to housekeeping staff with priority
- Status: `pending` → `in progress` → `completed`

### Maintenance Tickets
In-house maintenance requests:
- Categories: plumbing, electrical, HVAC, furniture, IT, general
- Priority and status tracking
- Cost estimates and actuals

### Service Requests
Guest in-room requests:
- Types: room service, towels, wake-up call, laundry, concierge, transport
- Assign to relevant department, track to completion

### Concierge Notes
Guest preference and VIP alert records: dietary requirements, loyalty status, special occasions, complaints.
